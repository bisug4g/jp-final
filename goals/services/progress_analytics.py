"""
Goal Progress Analytics Service
"""
from django.utils import timezone
from goals.models import Goal, Task
from collections import defaultdict


class GoalProgressService:
    """Analyze goal progress and generate chart data"""
    
    def __init__(self, user):
        self.user = user
    
    def get_overall_progress(self):
        """Get overall progress across all active goals"""
        active_goals = Goal.objects.filter(user=self.user, status='active')
        
        if not active_goals:
            return {
                'has_goals': False,
                'message': 'Create your first goal to track progress!'
            }
        
        total_progress = sum(g.completion_percentage for g in active_goals)
        avg_progress = total_progress / len(active_goals)
        
        return {
            'has_goals': True,
            'total_goals': len(active_goals),
            'avg_progress': round(avg_progress, 1),
            'goals': [
                {
                    'title': g.title,
                    'progress': g.completion_percentage,
                    'role': g.role_category,
                }
                for g in active_goals
            ]
        }
    
    def get_department_progress(self):
        """Get task completion by department"""
        tasks = Task.objects.filter(goal__user=self.user, goal__status='active')
        
        dept_stats = defaultdict(lambda: {'total': 0, 'done': 0})
        
        for task in tasks:
            dept_stats[task.department]['total'] += 1
            if task.status == 'done':
                dept_stats[task.department]['done'] += 1
        
        result = []
        for dept, stats in dept_stats.items():
            completion = (stats['done'] / stats['total'] * 100) if stats['total'] > 0 else 0
            result.append({
                'department': dept,
                'total': stats['total'],
                'completed': stats['done'],
                'completion_percentage': round(completion, 1),
            })
        
        return result
    
    def get_task_status_distribution(self):
        """Get distribution of task statuses"""
        tasks = Task.objects.filter(goal__user=self.user, goal__status='active')
        
        status_count = defaultdict(int)
        for task in tasks:
            status_count[task.status] += 1
        
        return dict(status_count)
    
    def get_timeline_progress(self):
        """Get progress over time (monthly)"""
        # This would track completion_percentage changes over time
        # For now, return current snapshot
        goals = Goal.objects.filter(user=self.user, status='active')
        
        return [
            {
                'goal': g.title,
                'progress': g.completion_percentage,
                'target_date': g.target_date.strftime('%Y-%m-%d'),
            }
            for g in goals
        ]


def get_progress_chart_data(user):
    """Get data formatted for Chart.js donut/pie charts"""
    service = GoalProgressService(user)
    
    # Department progress for donut chart
    dept_progress = service.get_department_progress()
    
    dept_chart = {
        'labels': [d['department'].title() for d in dept_progress],
        'data': [d['completion_percentage'] for d in dept_progress],
        'colors': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'],
    }
    
    # Task status distribution
    status_dist = service.get_task_status_distribution()
    
    status_chart = {
        'labels': [s.replace('_', ' ').title() for s in status_dist.keys()],
        'data': list(status_dist.values()),
        'colors': ['#FFA726', '#42A5F5', '#66BB6A', '#EF5350', '#AB47BC', '#FF7043'],
    }
    
    # Overall goal progress
    overall = service.get_overall_progress()
    
    if overall.get('has_goals'):
        goal_chart = {
            'labels': [g['title'][:30] for g in overall['goals']],
            'data': [g['progress'] for g in overall['goals']],
            'colors': ['#8E24AA', '#D81B60', '#F4511E', '#6D4C41', '#546E7A'],
        }
    else:
        goal_chart = {'labels': [], 'data': [], 'colors': []}
    
    return {
        'department': dept_chart,
        'status': status_chart,
        'goals': goal_chart,
        'overall': overall,
    }
