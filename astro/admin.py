from django.contrib import admin
from .models import BirthChart, PlanetPosition, HouseDetail, Prediction


class PlanetPositionInline(admin.TabularInline):
    model = PlanetPosition
    extra = 0


class HouseDetailInline(admin.TabularInline):
    model = HouseDetail
    extra = 0


@admin.register(BirthChart)
class BirthChartAdmin(admin.ModelAdmin):
    list_display = ['user', 'birth_date', 'birth_time', 'timezone', 'calculated_at']
    search_fields = ['user__username']
    readonly_fields = ['calculated_at']
    inlines = [PlanetPositionInline, HouseDetailInline]


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['birth_chart', 'period_type', 'start_date', 'focus_area', 'intensity']
    list_filter = ['period_type', 'focus_area', 'intensity']
    search_fields = ['birth_chart__user__username']
