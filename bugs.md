# Bugs

## Recently Fixed

Latest fixes (Fixed in current session):
- ✅ UV index stuck at 8 all day/night - was using daily maximum instead of current hourly UV value
- ✅ Odds text overlaps with team names. break it up into 2 lines, so if it is OKC -6.5 have OKC on one line and -6.5 on the next. Put this in the place the scores would normally be
- ✅ News headline text seems to be cut off after a certain number of characters
- ✅ ESPN betting line position is wrong as it is on top of the logo to the right, making it difficult to read. It is also cut off to the right.

News display (Fixed in commit 7040ed6):
- ✅ Each headline should finish scrolling before moving to the next one
- ✅ The contrast of the logo isn't great, the NYT logo for example is too dim. Should boost contrast somehow.

ESPN (Fixed in commit 7040ed6):
- ✅ The logos seem to be different sizes. For example the OKC Thunder logo is significantly smaller than the Indiana Pacers logo. This may be due to how they're sized in the images from ESPN, but correcting for this would be nice to have.

Bay Wheels (all fixed in latest commit):
- ✅ Text positioning and scroll issues
- ✅ Blank screen from offset problems  
- ✅ Icon size upgraded to 9x9 with proper positioning
- ✅ Station text display improved with rotation system