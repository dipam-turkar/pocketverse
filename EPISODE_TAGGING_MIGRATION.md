# Episode Tagging Migration Notes

## Existing Data Handling

### Existing Posts
- **Status**: All existing posts have `NULL` values for `show_name` and `episode_tag`
- **Behavior**: Posts with `NULL` values are visible to **all users** (no filtering applied)
- **Rationale**: This ensures backward compatibility - existing posts remain accessible to everyone
- **Action Required**: None. Existing posts will continue to work as before.

### Existing Users
- **Status**: Existing users may or may not have `watched_shows` data
- **Behavior**: 
  - Users without `watched_shows` will see all posts (including tagged ones)
  - Users with `watched_shows` will see filtered posts based on their watched episodes
- **Action Required**: Users can update their watched episodes via:
  - `/api/auth/update_watched` endpoint
  - Registration form (for new users)
  - Profile settings (if implemented)

## New Features

### Post Creation
- Posts can now be tagged with:
  - `show_name`: The show this post relates to
  - `episode_tag`: The episode number (prevents spoilers)
- Tagged posts are filtered based on user's `watched_shows`
- Untagged posts (NULL values) are visible to everyone

### User Registration
- New users can set their initial watched shows during registration
- Users can add multiple shows with their current episode numbers
- This prevents them from seeing spoilers from episodes they haven't watched

## Database Schema Changes

### Posts Table
- Added `show_name` VARCHAR(200) - nullable, indexed
- Added `episode_tag` INTEGER - nullable, indexed

### Migration
- Migration script: `migrate_add_episode_tagging.py`
- Run with: `python3 migrate_add_episode_tagging.py`
- Creates indexes for query performance

## Filtering Logic

Posts are shown to users if:
1. Post has no `show_name`/`episode_tag` (untagged) - **visible to all**
2. Post's `show_name` is not in user's `watched_shows` (different show) - **visible to all**
3. Post's `show_name` is in user's `watched_shows` AND `episode_tag <= user's watched episode` - **visible if user has watched that episode or later**

This ensures users don't see spoilers from episodes they haven't watched yet.

