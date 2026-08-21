@echo off
setlocal

for /f "tokens=1" %%B in ('usbipd list ^| findstr /i "0483:374b"') do (
    set "STM_BUSID=%%B"
    goto :stm_found
)

echo Situation STM was not found.
echo Connect the STM32 USB cable and try again.
pause
exit /b 1

:stm_found
echo Situation STM BUSID: %STM_BUSID%
echo Attaching STM32 to WSL...

usbipd attach --wsl --busid %STM_BUSID%

echo Starting station_node...
wsl -d Ubuntu-24.04 -- /home/lthst/run_station.sh

echo.
echo station_node stopped.
pause