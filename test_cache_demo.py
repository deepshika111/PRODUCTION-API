from app.cache import ResponseCache
import time 

cache = ResponseCache(ttl_seconds=3)  # short TTL for demo

print('=== CACHE DEMO ===')
print()

# Miss
result = cache.get('What is Python?')
print(f'1. First lookup: {result}  (miss - nothing cached yet)')

# Store
cache.set('What is Python?', 'Python is a programming language.')
print('2. Stored response in cache')

# Hit
result = cache.get('What is Python?')
print(f'3. Second lookup: {result}  (HIT!)')
print()

# Stats
print(f'4. Stats: {cache.stats}')
print()

# TTL expiry
print('5. Waiting 4s for TTL to expire...')
time.sleep(4)
result = cache.get('What is Python?')
print(f'6. Third lookup: {result}  (miss - entry expired)')
print()

print(f'7. Final stats: {cache.stats}')

