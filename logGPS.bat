@echo off
color A
title GPS monitor
SET /P runtime="GPS monitor - enter time to acquire (min): "
title GPS monitor started at %time% running for %runtime% min
python gpsMonitor.py 192.168.1.121 -d -t %runtime% -l gpslog
echo.
echo ************************************************************
echo * Acquisition cycle complete - press a key to close window *
echo ************************************************************
title GPS monitor acquisition complete
pause >nul