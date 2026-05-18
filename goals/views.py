from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import logging
import json
import re

from core.services.ai_runtime import AIConfigurationError, AIProviderError, generate_prompt_response

from .models import Goal, Task, Milestone

logger = logging.getLogger('goals')


@login_required
def goal_list(request):
    """List all goals with progress charts"""
    goals = Goal.objects.filter(user=request.user, status='active')
    completed_goals = Goal.objects.filter(user=request.user, status='completed')
    
    # Get all tasks for charts
    all_tasks = Task.objects.filter(goal__user=request.user)
    tasks_done = all_tasks.filter(status='done').count()
    tasks_in_progress = all_tasks.filter(status='in_progress').count()
    tasks_pending = all_tasks.filter(status__in=['pending', 'blocked', 'at_risk', 'overdue']).count()
    
    # Calculate overall completion percentage
    total_goals = goals.count() + completed_goals.count()
    if total_goals > 0:
        total_completion = sum(g.completion_percentage for g in goals) + (completed_goals.count() * 100)
        overall_completion = int(total_completion / total_goals)
    else:
        overall_completion = 0
    
    context = {
        'goals': goals,
        'completed_goals': completed_goals,
        'total_active': goals.count(),
        'total_completed': completed_goals.count(),
        'tasks_done': tasks_done,
        'tasks_in_progress': tasks_in_progress,
        'tasks_pending': tasks_pending,
        'overall_completion': overall_completion,
    }
    return render(request, 'goals/goal_list.html', context)


@login_required
def goal_create(request):
    """Create a new goal with AI-powered task generation"""
    if request.method == 'POST':
        goal = Goal.objects.create(
            user=request.user,
            role_category=request.POST.get('role_category'),
            experience_level=request.POST.get('experience_level'),
            time_horizon=request.POST.get('time_horizon'),
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            target_date=request.POST.get('target_date'),
        )
        
        # AI-powered task generation
        try:
            ai_tasks = generate_ai_tasks(goal)
            if ai_tasks:
                messages.success(request, f'Goal created successfully. {len(ai_tasks)} AI-generated tasks have been added.')
            else:
                create_decomposed_tasks(goal)
                messages.info(request, 'Goal created successfully. AI returned an unusable plan, so a starter task list was created.')
        except (AIConfigurationError, AIProviderError) as exc:
            logger.warning("AI task generation unavailable for goal %s: %s", goal.pk, exc)
            create_decomposed_tasks(goal)
            messages.info(request, 'Goal created successfully. AI planning is unavailable, so a starter task list was created.')
        
        # Track activity
        try:
            from core.services.activity_tracker import record_goal_created
            record_goal_created(request.user)
        except Exception:
            pass
        
        return redirect('goal_detail', pk=goal.pk)
    
    return render(request, 'goals/goal_form.html')


def generate_ai_tasks(goal):
    """Generate tasks using a configured production AI provider."""
    role_display = dict(Goal._meta.get_field('role_category').choices).get(goal.role_category, 'Marketing')
    level_display = dict(Goal._meta.get_field('experience_level').choices).get(goal.experience_level, 'Mid Level')

    prompt = f"""Act as a Chief Marketing Officer (CMO) and career strategist. 

Create a structured action plan for a {level_display} professional in {role_display}.

GOAL: {goal.title}
DESCRIPTION: {goal.description or 'No description provided'}
TIME HORIZON: {goal.time_horizon}

Generate 6-8 specific, actionable tasks organized by corporate department:
- Strategy (strategic planning, market analysis)
- Finance (budgeting, ROI analysis)
- HR (skill development, networking)
- Operations (execution, tools setup)
- Sales (client acquisition, pitching)

For each task, provide:
1. Department (one of: strategy, finance, hr, operations, sales)
2. Title (clear, actionable)
3. Description (2-3 sentences)
4. Priority (high/medium/low)
5. Suggested timeframe (week 1-2, month 1, etc.)

Format as JSON-like structure:
[
  {{
    "department": "strategy",
    "title": "Task title",
    "description": "Detailed description",
    "priority": "high",
    "timeframe": "week 1"
  }}
]

Be specific, practical, and motivational. Focus on measurable outcomes."""

    completion = generate_prompt_response(
        prompt,
        max_tokens=800,
        temperature=0.7,
        top_p=0.9,
    )
    return parse_ai_response_to_tasks(completion.text, goal)


def parse_ai_response_to_tasks(ai_content, goal):
    """Parse AI response and create Task objects"""
    from datetime import datetime
    
    tasks = []
    today = timezone.now().date()
    
    cleaned_content = ai_content.strip()
    cleaned_content = re.sub(r'^```(?:json)?\s*', '', cleaned_content, flags=re.IGNORECASE)
    cleaned_content = re.sub(r'\s*```$', '', cleaned_content)

    json_match = re.search(r'\[[\s\S]*\]', cleaned_content)

    if json_match:
        try:
            task_data = json.loads(json_match.group())
        except json.JSONDecodeError:
            task_data = parse_manual_task_extraction(ai_content)
    else:
        object_match = re.search(r'\{[\s\S]*\}', cleaned_content)
        if object_match:
            try:
                parsed_object = json.loads(object_match.group())
                task_data = parsed_object.get('tasks') if isinstance(parsed_object, dict) else None
            except json.JSONDecodeError:
                task_data = parse_manual_task_extraction(ai_content)
        else:
            task_data = parse_manual_task_extraction(ai_content)
    
    if not task_data:
        return None
    
    # Create tasks from parsed data
    for i, task_info in enumerate(task_data[:8]):  # Max 8 tasks
        department = task_info.get('department', 'strategy').lower()
        if department not in ['strategy', 'finance', 'hr', 'operations', 'sales']:
            department = 'strategy'
        
        # Calculate due date based on timeframe
        timeframe = task_info.get('timeframe', 'week 1').lower()
        if 'week 1' in timeframe or 'immediate' in timeframe:
            due_date = today + timedelta(days=7)
        elif 'week 2' in timeframe:
            due_date = today + timedelta(days=14)
        elif 'month 1' in timeframe or '30' in timeframe:
            due_date = today + timedelta(days=30)
        elif 'month 2' in timeframe:
            due_date = today + timedelta(days=60)
        else:
            due_date = today + timedelta(days=7 + i*3)
        
        # Determine task frequency
        is_weekly = 'weekly' in timeframe or 'recurring' in task_info.get('description', '').lower()
        is_monthly = 'monthly' in timeframe
        
        task = Task.objects.create(
            goal=goal,
            department=department,
            title=task_info.get('title', f'Task {i+1}'),
            description=task_info.get('description', ''),
            due_date=due_date,
            is_weekly=is_weekly,
            is_monthly=is_monthly,
            status='pending'
        )
        tasks.append(task)
    
    return tasks


def parse_manual_task_extraction(ai_content):
    """Manual parsing if JSON extraction fails"""
    tasks = []
    lines = ai_content.split('\n')
    
    current_task = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for department indicators
        if any(dept in line.lower() for dept in ['strategy:', 'finance:', 'hr:', 'operations:', 'sales:']):
            if current_task.get('title'):
                tasks.append(current_task)
            current_task = {
                'department': line.split(':')[0].lower().strip(),
                'title': line.split(':', 1)[1].strip() if ':' in line else line,
                'description': '',
                'priority': 'medium',
                'timeframe': 'week 1'
            }
        elif current_task.get('title') and not current_task.get('description'):
            current_task['description'] = line
    
    if current_task.get('title'):
        tasks.append(current_task)
    
    return tasks if tasks else None


def create_decomposed_tasks(goal):
    """Create an explicit starter plan when AI planning is unavailable."""
    from datetime import datetime
    target = datetime.strptime(str(goal.target_date), '%Y-%m-%d').date()
    today = timezone.now().date()
    
    # Create milestone-based tasks based on time horizon
    if goal.time_horizon == '1year':
        milestones = [
            ('Q1: Foundation Building', 90),
            ('Q2: Skill Expansion', 180),
            ('Q3: Project Leadership', 270),
            ('Q4: Consolidation', 365),
        ]
    elif goal.time_horizon == '3year':
        milestones = [
            ('Year 1: Specialization', 365),
            ('Year 2: Leadership', 730),
            ('Year 3: Strategic Impact', 1095),
        ]
    else:
        milestones = [
            ('Phase 1: Foundation', 180),
            ('Phase 2: Growth', 365),
        ]
    
    for title, days in milestones:
        milestone_date = today + timedelta(days=min(days, (target - today).days))
        Milestone.objects.create(
            goal=goal,
            title=title,
            target_date=milestone_date
        )
    
    # Create some initial tasks
    departments = ['strategy', 'hr', 'operations']
    for i, dept in enumerate(departments):
        Task.objects.create(
            goal=goal,
            department=dept,
            title=f'Initial {dept.title()} assessment and planning',
            due_date=today + timedelta(days=7 + i*3),
            is_weekly=True,
        )


@login_required
def goal_detail(request, pk):
    """View goal details with tasks and progress charts"""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    tasks = goal.tasks.all()
    milestones = goal.milestones.all()
    
    # Group tasks by status
    tasks_by_status = {
        'done': tasks.filter(status='done'),
        'in_progress': tasks.filter(status='in_progress'),
        'pending': tasks.filter(status='pending'),
        'blocked': tasks.filter(status='blocked'),
        'at_risk': tasks.filter(status='at_risk'),
        'overdue': tasks.filter(status='overdue'),
    }
    
    # Calculate progress
    if tasks:
        completed = tasks.filter(status='done').count()
        new_percentage = int((completed / tasks.count()) * 100)
        if goal.completion_percentage != new_percentage:
            goal.completion_percentage = new_percentage
            goal.save(update_fields=['completion_percentage'])
    
    # Task counts for charts
    tasks_done_count = tasks.filter(status='done').count()
    tasks_in_progress_count = tasks.filter(status='in_progress').count()
    tasks_pending_count = tasks.filter(status__in=['pending', 'at_risk', 'overdue']).count()
    tasks_blocked_count = tasks.filter(status='blocked').count()
    
    # Department distribution for charts
    dept_strategy = tasks.filter(department='strategy').count()
    dept_finance = tasks.filter(department='finance').count()
    dept_hr = tasks.filter(department='hr').count()
    dept_operations = tasks.filter(department='operations').count()
    dept_sales = tasks.filter(department='sales').count()
    tasks_by_department = []
    for code, label in Task.DEPARTMENTS:
        department_tasks = tasks.filter(department=code)
        if department_tasks.exists():
            tasks_by_department.append({
                'code': code,
                'label': label,
                'tasks': department_tasks,
                'completed': department_tasks.filter(status='done').count(),
                'count': department_tasks.count(),
            })
    
    context = {
        'goal': goal,
        'tasks': tasks,
        'milestones': milestones,
        'tasks_by_status': tasks_by_status,
        'tasks_by_department': tasks_by_department,
        # Chart data
        'tasks_done_count': tasks_done_count,
        'tasks_in_progress_count': tasks_in_progress_count,
        'tasks_pending_count': tasks_pending_count,
        'tasks_blocked_count': tasks_blocked_count,
        'dept_strategy': dept_strategy,
        'dept_finance': dept_finance,
        'dept_hr': dept_hr,
        'dept_operations': dept_operations,
        'dept_sales': dept_sales,
    }
    return render(request, 'goals/goal_detail.html', context)


@login_required
def goal_edit(request, pk):
    """Edit a goal"""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    
    if request.method == 'POST':
        goal.role_category = request.POST.get('role_category')
        goal.experience_level = request.POST.get('experience_level')
        goal.time_horizon = request.POST.get('time_horizon')
        goal.title = request.POST.get('title')
        goal.description = request.POST.get('description', '')
        goal.target_date = request.POST.get('target_date')
        goal.status = request.POST.get('status', 'active')
        goal.save()
        
        messages.success(request, 'Goal updated successfully.')
        return redirect('goal_detail', pk=goal.pk)
    
    return render(request, 'goals/goal_form.html', {'goal': goal})


@login_required
def goal_delete(request, pk):
    """Delete a goal"""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    
    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Goal deleted successfully.')
        return redirect('goal_list')
    
    return render(request, 'goals/goal_confirm_delete.html', {'goal': goal})


@login_required
def task_create(request, goal_pk):
    """Create a new task"""
    goal = get_object_or_404(Goal, pk=goal_pk, user=request.user)
    
    if request.method == 'POST':
        Task.objects.create(
            goal=goal,
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            department=request.POST.get('department', 'strategy'),
            due_date=request.POST.get('due_date'),
            is_quarterly=request.POST.get('is_quarterly') == 'on',
            is_monthly=request.POST.get('is_monthly') == 'on',
            is_weekly=request.POST.get('is_weekly') == 'on',
            is_daily=request.POST.get('is_daily') == 'on',
        )
        messages.success(request, 'Task created successfully.')
        return redirect('goal_detail', pk=goal.pk)
    
    return render(request, 'goals/task_form.html', {'goal': goal})


@login_required
def task_update(request, pk):
    """Update task status"""
    task = get_object_or_404(Task, pk=pk, goal__user=request.user)
    
    if request.method == 'POST':
        old_status = task.status
        task.status = request.POST.get('status')
        task.completion_percentage = int(request.POST.get('completion_percentage', 0))
        
        if task.status == 'done':
            task.completion_percentage = 100
            task.completed_at = timezone.now()
            
            # Track task completion activity
            if old_status != 'done':
                try:
                    from core.services.activity_tracker import record_task_completed
                    record_task_completed(request.user)
                except Exception:
                    pass
        
        if task.status == 'blocked':
            task.blocked_reason = request.POST.get('blocked_reason', '')
        
        task.save()
        messages.success(request, 'Task updated successfully.')
        return redirect('goal_detail', pk=task.goal.pk)
    
    return render(request, 'goals/task_update.html', {'task': task})


@login_required
def task_delete(request, pk):
    """Delete a task"""
    task = get_object_or_404(Task, pk=pk, goal__user=request.user)
    goal_pk = task.goal.pk
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully.')
        return redirect('goal_detail', pk=goal_pk)
    
    return render(request, 'goals/task_confirm_delete.html', {'task': task})


@login_required
def goal_board(request):
    """Kanban-style board view"""
    goals = Goal.objects.filter(user=request.user, status='active')
    
    # Get all tasks grouped by status
    tasks = Task.objects.filter(goal__user=request.user)
    
    context = {
        'goals': goals,
        'tasks': tasks,
        'tasks_done': tasks.filter(status='done'),
        'tasks_in_progress': tasks.filter(status='in_progress'),
        'tasks_pending': tasks.filter(status='pending'),
        'tasks_blocked': tasks.filter(status='blocked'),
    }
    return render(request, 'goals/goal_board.html', context)


@login_required
def regenerate_ai_tasks(request, pk):
    """Regenerate AI tasks for an existing goal"""
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Clear existing tasks
        goal.tasks.all().delete()
        
        try:
            ai_tasks = generate_ai_tasks(goal)
            if ai_tasks:
                messages.success(request, f'{len(ai_tasks)} new AI-generated tasks have been created.')
            else:
                create_decomposed_tasks(goal)
                messages.info(request, 'AI returned an unusable plan, so a starter task list was created.')
        except (AIConfigurationError, AIProviderError) as exc:
            logger.warning("AI regeneration unavailable for goal %s: %s", goal.pk, exc)
            create_decomposed_tasks(goal)
            messages.warning(request, 'AI planning is unavailable, so a starter task list was created.')
        
        return redirect('goal_detail', pk=goal.pk)
    
    return render(request, 'goals/regenerate_tasks.html', {'goal': goal})
