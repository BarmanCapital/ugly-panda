from django.contrib import admin

from tgbot.models import MeUser, StudySentence, UserActivity, UserStudyRecord

# Register your models here.

@admin.register(MeUser)
class MeUserAdmin(admin.ModelAdmin):

    list_display = ('user_id', 'username', 'points', 'tons', 'refer_user_id', 'created_time', 'updated_time')
    search_fields = ('username', )
    readonly_fields = ('created_time', 'updated_time')
    ordering = ('-created_time',)


@admin.register(StudySentence)
class StudySentenceAdmin(admin.ModelAdmin):

    list_display = ('text_eng', 'send_time', 'is_sent')
    search_fields = ('text_eng', )
    readonly_fields = ('created_time', 'updated_time')
    ordering = ('-created_time',)


@admin.register(UserStudyRecord)
class UserStudyRecordAdmin(admin.ModelAdmin):

    list_display = ('user', 'sentence', 'points', 'time', 'type', 'updated_time')
    search_fields = ('user__username', )
    readonly_fields = ('created_time', 'updated_time')
    ordering = ('-created_time',)


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'sats', 'type', 'tons', 'desc', 'created_time')
    search_fields = ('user__username', )
    list_filter = ("desc", )
    readonly_fields = ('created_time', 'updated_time')
    ordering = ('-created_time',)

