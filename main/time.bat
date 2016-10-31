set hh=%time:~0,2%

set mm=%time:~3,2%



set /A mm=%mm%+2



if %mm% GTR 60 set /A mm=%mm%-60 && set /A hh=%hh%+1

if %hh% GTR 24 set hh=00



set hhmm=%hh%:%mm%



echo %hhmm%
