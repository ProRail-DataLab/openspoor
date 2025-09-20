# Route Interface Refactoring Example

This example demonstrates the refactored route interface that provides a comprehensive 
value object instead of requiring multiple separate method calls.

## Before (Complex Interface)
```python
# Previously, getting complete route information required multiple calls:
route = track_netherlands.dijkstra(start, end)

# Multiple separate calls needed:
distance = route.length  # or some distance method
segments = some_method_to_get_segments(route) 
travel_time = some_travel_time_calculator(route)
summary = combine_all_data_manually(distance, segments, travel_time)
```

## After (Single Comprehensive Value Object)
```python
# Now, all route information is available in a single comprehensive object:
route = track_netherlands.dijkstra(start, end)  # Returns enhanced Route object

# All information available through one consistent interface:
print(f"Distance: {route.distance_km} km")
print(f"Travel time: {route.total_travel_time} minutes") 
print(f"Segments: {len(route.route_segments)}")

# Detailed segment information:
for segment in route.route_segments:
    print(f"Segment {segment['puic']}: {segment['length_km']} km, {segment['estimated_time_minutes']} min")

# Complete summary in one call:
summary = route.summary  # Dictionary with all route metrics
```

## Benefits

1. **Single Value Object**: All route information in one comprehensive object
2. **Reduced Complexity**: No need for multiple endpoint calls or data assembly
3. **Consistent Interface**: All route metrics available through the same object
4. **Backward Compatible**: Existing code continues to work unchanged
5. **Enhanced Functionality**: New capabilities like travel time estimation and detailed segments

## Implementation

The enhanced `Route` class now provides:
- `distance` / `distance_km` - Total route distance
- `total_travel_time` - Estimated travel time in minutes
- `route_segments` - Detailed information for each track segment
- `summary` - Complete route summary with all metrics
- `segment_count` - Number of track segments

All while maintaining existing functionality like `length`, `set_color()`, and visualization methods.