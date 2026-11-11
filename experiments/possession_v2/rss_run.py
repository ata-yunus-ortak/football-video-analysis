"""Run a command; print its exit code, wall time and the largest resident memory of any (grand)child."""
import resource, subprocess, sys, time
t = time.time()
code = subprocess.call(sys.argv[1:])
print(f'[exit {code}; {time.time() - t:.0f} s; peak child RSS {resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1e6:.2f} GB]', flush=True)
sys.exit(code)
