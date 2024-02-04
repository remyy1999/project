Problems Encountered and Solutions

Connection Timeout Problem: script was experiencing delays during the connection phase. Solution: 10-second timeout for the connection to prevent prolonged waits.

Emulated Delays Problem: Needed to introduce delays to simulate network latency. Solution: Incorporated a 100 milliseconds sleep between sending file chunks.

Transmission Errors Problem: Simulating transmission errors based on a probability. Solution: Implemented a 10% probability of error during file transmission.

File Not Found Problem: Handling scenarios where the specified file is not found. Solution: Added exception handling

Acknowledgments

Proffesor module lectures/tutorials, Many yourube videos, additional videos given by professsor, various coding forums
