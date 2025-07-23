from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import logging
import json

from src.api.core.logging_config import get_logger

logger = get_logger("restaurant_api")


class ConnectionManager:
    """
    WebSocket connection manager for handling real-time updates.
    
    This class provides functionality to:
    - Connect new WebSocket clients
    - Disconnect clients
    - Send messages to specific clients or groups
    - Broadcast messages to all clients
    """
    
    def __init__(self):
        # Store connections by client_id (reconciliation_id, etc.)
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """
        Add a new WebSocket connection to the manager.
        
        Args:
            websocket: WebSocket connection
            client_id: Unique identifier for the client (e.g. reconciliation_id)
        """
        # Accept the connection
        await websocket.accept()
        
        # Initialize client list if this is a new client_id
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
            
        # Add this connection to the client's list
        self.active_connections[client_id].append(websocket)
        logger.debug(f"WebSocket client connected: {client_id}")
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        """
        Remove a WebSocket connection from the manager.
        
        Args:
            websocket: WebSocket connection to remove
            client_id: Client identifier
        """
        if client_id in self.active_connections:
            # Remove this specific connection
            self.active_connections[client_id].remove(websocket)
            
            # If no more connections for this client_id, remove the entry
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
                
            logger.debug(f"WebSocket client disconnected: {client_id}")
    
    async def send_message(self, message: dict, client_id: str):
        """
        Send a message to all connections for a specific client_id.
        
        Args:
            message: Message to send (will be converted to JSON)
            client_id: Client identifier
        """
        if client_id in self.active_connections:
            inactive_connections = []
            
            # Attempt to send to each connection for this client
            for i, connection in enumerate(self.active_connections[client_id]):
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to client {client_id}: {str(e)}")
                    inactive_connections.append(i)
            
            # Clean up any connections that failed (in reverse to avoid index issues)
            for i in sorted(inactive_connections, reverse=True):
                self.active_connections[client_id].pop(i)
                
            # If we removed all connections, remove the client entry
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
    
    async def broadcast(self, message: dict):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Message to broadcast (will be converted to JSON)
        """
        # Get all unique websockets across all client_ids
        all_connections = set()
        for connections in self.active_connections.values():
            for connection in connections:
                all_connections.add(connection)
        
        # Send to each connection
        inactive_connections = []
        for connection in all_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {str(e)}")
                inactive_connections.append(connection)
        
        # Clean up failed connections
        for connection in inactive_connections:
            for client_id, connections in list(self.active_connections.items()):
                if connection in connections:
                    connections.remove(connection)
                    if not connections:
                        del self.active_connections[client_id]


# Create a singleton instance
connection_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """
    Get the global connection manager instance.
    
    Returns:
        ConnectionManager: The global connection manager
    """
    return connection_manager