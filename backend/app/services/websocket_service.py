"""
WebSocket Service for Real-Time Updates
========================================
Provides WebSocket connections for live market data, news, and signals.
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
import json
import logging
from datetime import datetime
import asyncio
from typing import Dict, Any, Optional, Callable
import threading
import time

logger = logging.getLogger(__name__)

# Initialize SocketIO
socketio: Optional[SocketIO] = None

# Connected clients tracking
connected_clients: Dict[str, Dict[str, Any]] = {}

# Subscriptions tracking
subscriptions: Dict[str, set] = {
    'market': set(),
    'news': set(),
    'signals': set(),
    'alerts': set()
}

# Background thread for broadcasting
def init_socketio(app, cors_allowed_origins="*"):
    """Initialize SocketIO with Flask app"""
    global socketio
    socketio = SocketIO(
        app,
        cors_allowed_origins=cors_allowed_origins,
        async_mode='threading',
        logger=True,
        engineio_logger=True
    )
    return socketio


class WebSocketManager:
    """Manages WebSocket connections and broadcasting"""
    
    @staticmethod
    def handle_connect():
        """Handle client connection"""
        client_id = request.sid
        connected_clients[client_id] = {
            'connected_at': datetime.utcnow().isoformat(),
            'subscriptions': set(),
            'client_info': request.headers.get('User-Agent', 'Unknown')
        }
        logger.info(f"Client {client_id} connected")
        emit('connected', {'client_id': client_id, 'status': 'connected'})
    
    @staticmethod
    def handle_disconnect():
        """Handle client disconnection"""
        client_id = request.sid
        if client_id in connected_clients:
            # Remove from all subscriptions
            for room in list(connected_clients[client_id]['subscriptions']):
                leave_room(room)
                subscriptions[room].discard(client_id)
            del connected_clients[client_id]
        logger.info(f"Client {client_id} disconnected")
    
    @staticmethod
    def handle_subscribe(data: Dict[str, Any]):
        """Handle subscription request"""
        client_id = request.sid
        channel = data.get('channel', 'market')
        
        if channel in subscriptions:
            join_room(channel)
            subscriptions[channel].add(client_id)
            connected_clients[client_id]['subscriptions'].add(channel)
            
            emit('subscribed', {
                'channel': channel,
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat()
            })
            logger.info(f"Client {client_id} subscribed to {channel}")
        else:
            emit('error', {'message': f'Unknown channel: {channel}'})
    
    @staticmethod
    def handle_unsubscribe(data: Dict[str, Any]):
        """Handle unsubscription request"""
        client_id = request.sid
        channel = data.get('channel', 'market')
        
        if channel in subscriptions:
            leave_room(channel)
            subscriptions[channel].discard(client_id)
            connected_clients[client_id]['subscriptions'].discard(channel)
            
            emit('unsubscribed', {
                'channel': channel,
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat()
            })
    
    @staticmethod
    def broadcast_market_update(data: Dict[str, Any]):
        """Broadcast market data update"""
        if socketio and subscriptions['market']:
            socketio.emit('market_update', {
                'type': 'market',
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            }, room='market', broadcast=True)
    
    @staticmethod
    def broadcast_news_update(news_item: Dict[str, Any]):
        """Broadcast news update"""
        if socketio and subscriptions['news']:
            socketio.emit('news_update', {
                'type': 'news',
                'data': news_item,
                'timestamp': datetime.utcnow().isoformat()
            }, room='news', broadcast=True)
    
    @staticmethod
    def broadcast_signal(signal: Dict[str, Any]):
        """Broadcast trading signal"""
        if socketio and subscriptions['signals']:
            socketio.emit('signal', {
                'type': 'signal',
                'data': signal,
                'timestamp': datetime.utcnow().isoformat()
            }, room='signals', broadcast=True)
    
    @staticmethod
    def broadcast_alert(alert: Dict[str, Any]):
        """Broadcast alert to all clients"""
        if socketio and subscriptions['alerts']:
            socketio.emit('alert', {
                'type': 'alert',
                'data': alert,
                'timestamp': datetime.utcnow().isoformat()
            }, room='alerts', broadcast=True)
    
    @staticmethod
    def send_to_client(client_id: str, event: str, data: Dict[str, Any]):
        """Send message to specific client"""
        if socketio:
            socketio.emit(event, data, to=client_id)
    
    @staticmethod
    def get_client_stats() -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            'connected_clients': len(connected_clients),
            'subscriptions': {
                channel: len(clients) for channel, clients in subscriptions.items()
            },
            'clients': [
                {
                    'id': cid,
                    'connected_at': info['connected_at'],
                    'subscriptions': list(info['subscriptions'])
                }
                for cid, info in connected_clients.items()
            ]
        }


def start_background_broadcaster(interval: int = 5):
    """Start background thread to broadcast market data"""
    def broadcaster():
        while True:
            try:
                time.sleep(interval)
                
                # Only broadcast if there are subscribers
                if subscriptions['market']:
                    # Fetch latest market data from unified bridge
                    try:
                        from ..services.unified_data_bridge import get_market_indices
                        import asyncio
                        
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        indices = loop.run_until_complete(get_market_indices())
                        loop.close()
                        
                        if indices:
                            WebSocketManager.broadcast_market_update({
                                'indices': indices.get('indices', [])[:5],
                                'status': 'live'
                            })
                    except Exception as e:
                        logger.debug(f"Market broadcast skipped: {e}")
                        
            except Exception as e:
                logger.error(f"Broadcaster error: {e}")
    
    thread = threading.Thread(target=broadcaster, daemon=True)
    thread.start()
    logger.info("Background broadcaster started")


# Decorator for SocketIO event handlers
def register_handlers(socketio_instance: SocketIO):
    """Register all WebSocket event handlers"""
    
    @socketio_instance.on('connect')
    def on_connect():
        WebSocketManager.handle_connect()
    
    @socketio_instance.on('disconnect')
    def on_disconnect():
        WebSocketManager.handle_disconnect()
    
    @socketio_instance.on('subscribe')
    def on_subscribe(data):
        WebSocketManager.handle_subscribe(data)
    
    @socketio_instance.on('unsubscribe')
    def on_unsubscribe(data):
        WebSocketManager.handle_unsubscribe(data)
    
    @socketio_instance.on('ping')
    def on_ping():
        emit('pong', {'timestamp': datetime.utcnow().isoformat()})
    
    @socketio_instance.on('get_stats')
    def on_get_stats():
        emit('stats', WebSocketManager.get_client_stats())


# Convenience functions
def broadcast_market(data: Dict[str, Any]):
    """Broadcast market update"""
    WebSocketManager.broadcast_market_update(data)

def broadcast_news(news_item: Dict[str, Any]):
    """Broadcast news update"""
    WebSocketManager.broadcast_news_update(news_item)

def broadcast_signal(signal: Dict[str, Any]):
    """Broadcast signal"""
    WebSocketManager.broadcast_signal(signal)

def broadcast_alert(alert: Dict[str, Any]):
    """Broadcast alert"""
    WebSocketManager.broadcast_alert(alert)

def get_stats() -> Dict[str, Any]:
    """Get WebSocket stats"""
    return WebSocketManager.get_client_stats()


__all__ = [
    'init_socketio', 'register_handlers', 'start_background_broadcaster',
    'WebSocketManager', 'broadcast_market', 'broadcast_news',
    'broadcast_signal', 'broadcast_alert', 'get_stats'
]
