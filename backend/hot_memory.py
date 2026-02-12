import redis
import json
import hashlib
import time

class HotMemory:
    def __init__(self, host='localhost', port=6379, db=0):
        # We also keep a local fallback in case Redis isn't running
        self.local_cache = {}
        self.local_trends = {}
        self.use_local = False
        
        try:
            self.r = redis.Redis(
                host=host, 
                port=port, 
                db=db, 
                decode_responses=True,
                socket_connect_timeout=0.5 # Fast fail
            )
            self.r.ping()
            self.is_connected = True
            print("✓ Connected to Redis (High-Speed Mode)")
        except Exception:
            print("⚠ Redis Server not found. Running in Local High-Speed Mode (In-Memory).")
            self.is_connected = False
            self.use_local = True

    def get_query_hash(self, user_id, message):
        content = f"{user_id}:{message.strip().lower()}"
        return hashlib.md5(content.encode()).hexdigest()

    def check_cache(self, user_id, message):
        qh = self.get_query_hash(user_id, message)
        
        if self.is_connected:
            try:
                cached = self.r.get(f"cache:response:{qh}")
                if cached:
                    print(f"🚀 REDIS FAST PATH: Hit for '{message[:30]}...'")
                    return json.loads(cached)
            except: pass
        
        if qh in self.local_cache:
            # Check TTL for local cache
            entry = self.local_cache[qh]
            if time.time() < entry['expiry']:
                print(f"🚀 LOCAL FAST PATH: Hit for '{message[:30]}...'")
                return entry['data']
            else:
                del self.local_cache[qh]
                
        return None

    def save_to_cache(self, user_id, message, response_data, ttl=3600):
        qh = self.get_query_hash(user_id, message)
        
        if self.is_connected:
            try:
                self.r.setex(f"cache:response:{qh}", ttl, json.dumps(response_data))
                print(f"✔ Saved to Redis Hot Layer")
            except: pass
            
        self.local_cache[qh] = {
            'data': response_data,
            'expiry': time.time() + ttl
        }
        print(f"✔ Saved to Local Hot Layer (TTL: {ttl}s)")

    def track_trends(self, user_id, search_terms):
        if not search_terms: return
            
        for term in search_terms:
            if self.is_connected:
                try:
                    self.r.zincrby("trending:global", 1, term)
                except: pass
            
            # Local trend tracking
            self.local_trends[term] = self.local_trends.get(term, 0) + 1
            
    def get_trending(self, limit=5):
        if self.is_connected:
            try:
                return self.r.zrevrange("trending:global", 0, limit-1, withscores=True)
            except: pass
        
        # Sort local trends by value
        sorted_trends = sorted(self.local_trends.items(), key=lambda x: x[1], reverse=True)
        return sorted_trends[:limit]
