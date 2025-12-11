from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification

@login_required
def notification_list(request):
    """Liste complète des notifications"""
    notifications = request.user.notifications.all()
    
    # Marquer tout comme lu si demandé via POST
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return redirect('notifications:notification_list')

    context = {
        'notifications': notifications,
    }
    return render(request, 'notifications/notification_list.html', context)

@login_required
def mark_read(request, pk):
    """Marquer une notification comme lue et rediriger"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    
    if notification.related_case:
        return redirect('cases:case_detail', pk=notification.related_case.pk)
    
    return redirect('notifications:notification_list')

@login_required
def get_unread_count(request):
    """API pour le badge de notification"""
    count = Notification.get_unread_count(request.user)
    return JsonResponse({'count': count})
