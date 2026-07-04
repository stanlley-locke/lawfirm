// Admin Chat Dashboard JavaScript

// Update chat statistics
function updateChatStats() {
    // Fetch unread messages count
    fetch('/admin/chat/unread-count')
        .then(response => response.json())
        .then(data => {
            const unreadCountElement = document.getElementById('unread-chat-count');
            if (unreadCountElement) {
                unreadCountElement.textContent = data.count;
            }
        })
        .catch(error => console.error('Error fetching unread count:', error));
    
    // Fetch active chats count
    fetch('/admin/chat/active-count')
        .then(response => response.json())
        .then(data => {
            const activeChatsElement = document.getElementById('active-chats-count');
            if (activeChatsElement) {
                activeChatsElement.textContent = data.count;
            }
        })
        .catch(error => console.error('Error fetching active chats count:', error));
}

// Update the navigation badge for unread messages
function updateNavBadge() {
    fetch('/admin/chat/unread-count')
        .then(response => response.json())
        .then(data => {
            // Update sidebar badge
            const sidebarBadge = document.getElementById('chat-sidebar-badge');
            if (sidebarBadge) {
                if (data.count > 0) {
                    sidebarBadge.textContent = data.count;
                    sidebarBadge.classList.remove('d-none');
                } else {
                    sidebarBadge.classList.add('d-none');
                }
            }
            
            // Update topbar badge
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
    // Update chat stats immediately and then every 30 seconds
    updateChatStats();
    updateNavBadge();
    
    setInterval(() => {
        updateChatStats();
        updateNavBadge();
    }, 30000);
});