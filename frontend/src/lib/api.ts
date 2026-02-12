const API_URL = "http://localhost:8000";

export async function getConversations(userId: string) {
    try {
        const res = await fetch(`${API_URL}/conversations/${userId}`);
        if (!res.ok) {
            console.warn(`Failed to fetch conversations for ${userId}: ${res.status}`);
            return [];
        }
        return await res.json();
    } catch (error) {
        console.error("Error fetching conversations:", error);
        return [];
    }
}

export async function getMessages(conversationId: string) {
    try {
        const res = await fetch(`${API_URL}/conversations/${conversationId}/messages`);
        if (!res.ok) {
            console.warn(`Failed to fetch messages for ${conversationId}: ${res.status}`);
            return [];
        }
        return await res.json();
    } catch (error) {
        console.error("Error fetching messages:", error);
        return [];
    }
}

export async function createConversation(userId: string, title: string = "New Chat") {
    const res = await fetch(`${API_URL}/conversations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, title })
    });
    if (!res.ok) throw new Error("Failed to create conversation");
    return res.json();
}

export async function deleteConversation(conversationId: string) {
    const res = await fetch(`${API_URL}/conversations/${conversationId}`, {
        method: "DELETE"
    });
    if (!res.ok) throw new Error("Failed to delete conversation");
    return res.json();
}

export async function updateConversationTitle(conversationId: string, title: string) {
    const res = await fetch(`${API_URL}/conversations/${conversationId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title })
    });
    if (!res.ok) throw new Error("Failed to update conversation title");
    return res.json();
}
