// Admin Chat Dashboard JavaScript

let chatPollInterval = null;

function isAdminContext() {
    return Boolean(
        document.querySelector('.admin-dashboard-container') ||
        document.getElementById('chat-sidebar-badge') ||
        document.getElementById('topbar-chat-badge')
    );
}

function stopChatPolling() {
    if (chatPollInterval !== null) {
        clearInterval(chatPollInterval);
        chatPollInterval = null;
    }
}

function fetchAdminChatJson(url) {
    return fetch(url, { credentials: 'same-origin' })
        .then(response => {
            if (response.status === 401 || response.status === 403 || response.redirected) {
                stopChatPolling();
                return null;
            }
            if (!response.ok) {
                return null;
            }
            const contentType = response.headers.get('content-type') || '';
            if (!contentType.includes('application/json')) {
                stopChatPolling();
                return null;
            }
            return response.json();
        });
}

// Update chat statistics
function updateChatStats() {
    fetchAdminChatJson('/admin/chat/unread-count')
        .then(data => {
            if (!data) {
                return;
            }
            const unreadCountElement = document.getElementById('unread-chat-count');
            if (unreadCountElement) {
                unreadCountElement.textContent = data.count;
            }
        })
        .catch(error => console.error('Error fetching unread count:', error));

    fetchAdminChatJson('/admin/chat/active-count')
        .then(data => {
            if (!data) {
                return;
            }
            const activeChatsElement = document.getElementById('active-chats-count');
            if (activeChatsElement) {
                activeChatsElement.textContent = data.count;
            }
        })
        .catch(error => console.error('Error fetching active chats count:', error));
}

// Update the navigation badge for unread messages
function updateNavBadge() {
    fetchAdminChatJson('/admin/chat/unread-count')
        .then(data => {
            if (!data) {
                return;
            }

            const sidebarBadge = document.getElementById('chat-sidebar-badge');
            if (sidebarBadge) {
                if (data.count > 0) {
                    sidebarBadge.textContent = data.count;
                    sidebarBadge.classList.remove('d-none');
                } else {
                    sidebarBadge.classList.add('d-none');
                }
            }

            const topbarBadge = document.getElementById('topbar-chat-badge');
            if (topbarBadge) {
                if (data.count > 0) {
                    topbarBadge.textContent = data.count;
                    topbarBadge.classList.remove('d-none');
                } else {
                    topbarBadge.classList.add('d-none');
                }
            }
        })
        .catch(error => console.error('Error updating nav badge:', error));
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    if (!isAdminContext()) {
        return;
    }

    updateChatStats();
    updateNavBadge();

    chatPollInterval = setInterval(() => {
        updateChatStats();
        updateNavBadge();
    }, 30000);
});
