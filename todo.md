
# Completed Tasks

All tasks completed as of current session.

## Recently Completed

Latest fixes (Fixed in current session):
- ✅ For ESPN module, skip games more than a week away
- ✅ For the news ticker, the ticker starts with a blank screen and then starts scrolling the headline in from the right. Instead, when a new headline is shown it should start all the way to the left, and then after a couple seconds start scrolling.

ESPN display (Fixed in commit 7040ed6):
- ✅ Only the first game is shown right now. We should track what games have already been shown and skip to the next one the next time around.
- ✅ The logos are getting cut off on right side. They should be repositioned to show the full logo on the side next to the score, but their start position can be a little off-screen
- ✅ Don't show the scores when the game hasn't started yet. Instead, show the betting line information if available in the ESPN API.

Overall todos (Fixed in commit 7040ed6):
- ✅ Not all of the different data sources should necessarily be the same length of time as we cycle through. I think the data source themselves should have a method to determine how long it should display for. For now these can be static, e.g. 30 seconds, 10 seconds. In the future, we may want to make them dynamic (for example, ESPN should display longer when there are multiple games currently happening versus shorter when no games are currently happening)