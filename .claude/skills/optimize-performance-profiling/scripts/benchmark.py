#!/usr/bin/env python3
"""
Zero-Context Benchmark Script for Performance Profiling

Benchmarks JavaScript/TypeScript functions to measure performance.
Useful for comparing before/after optimization.

Usage:
    python benchmark.py --file src/utils.ts --function sortArray --iterations 1000
    python benchmark.py --before old.ts:oldFn --after new.ts:newFn --iterations 5000
"""

import argparse
import json
import subprocess
import sys
import statistics
from pathlib import Path
from typing import List, Dict, Optional


def create_benchmark_runner(
    file_path: str,
    function_name: str,
    iterations: int
) -> str:
    """Create a JavaScript benchmark runner script."""
    return f"""
// Auto-generated benchmark runner
const {{ performance }} = require('perf_hooks');

// Import the module
const module = require('./{file_path}');
const targetFunction = module.{function_name};

if (!targetFunction) {{
    console.error('Function "{function_name}" not found in {file_path}');
    process.exit(1);
}}

// Sample test data (customize based on function signature)
const testData = generateTestData();

function generateTestData() {{
    // Generate sample data - adjust based on your needs
    const arr = Array.from({{ length: 1000 }}, (_, i) => Math.random() * 1000);
    return arr;
}}

// Warmup phase (JIT compilation)
for (let i = 0; i < 100; i++) {{
    targetFunction(testData);
}}

// Actual benchmark
const timings = [];
const memoryBefore = process.memoryUsage().heapUsed;

for (let i = 0; i < {iterations}; i++) {{
    const start = performance.now();
    targetFunction(testData);
    const end = performance.now();
    timings.push(end - start);
}}

const memoryAfter = process.memoryUsage().heapUsed;
const memoryDelta = memoryAfter - memoryBefore;

// Calculate statistics
timings.sort((a, b) => a - b);

const results = {{
    iterations: {iterations},
    timings: {{
        average: timings.reduce((a, b) => a + b, 0) / timings.length,
        median: timings[Math.floor(timings.length / 2)],
        min: Math.min(...timings),
        max: Math.max(...timings),
        p95: timings[Math.floor(timings.length * 0.95)],
        p99: timings[Math.floor(timings.length * 0.99)]
    }},
    memory: {{
        delta: memoryDelta,
        deltaFormatted: (memoryDelta / 1024 / 1024).toFixed(2) + ' MB'
    }}
}};

console.log(JSON.stringify(results, null, 2));
"""


class BenchmarkRunner:
    """Runs performance benchmarks on JavaScript/TypeScript functions."""

    def __init__(self):
        self.temp_dir = Path('.benchmark_temp')
        self.temp_dir.mkdir(exist_ok=True)

    def cleanup(self):
        """Remove temporary files."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def run_benchmark(
        self,
        file_path: str,
        function_name: str,
        iterations: int
    ) -> Dict:
        """Run a single benchmark."""
        # Create benchmark runner script
        runner_code = create_benchmark_runner(file_path, function_name, iterations)
        runner_path = self.temp_dir / 'benchmark_runner.js'

        with open(runner_path, 'w') as f:
            f.write(runner_code)

        # Execute benchmark
        try:
            result = subprocess.run(
                ['node', str(runner_path)],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                print(f"Error running benchmark: {result.stderr}", file=sys.stderr)
                sys.exit(1)

            return json.loads(result.stdout)

        except subprocess.TimeoutExpired:
            print("Benchmark timed out (>60s)", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Failed to parse benchmark results: {e}", file=sys.stderr)
            print(f"Output: {result.stdout}", file=sys.stderr)
            sys.exit(1)

    def compare_benchmarks(
        self,
        before_result: Dict,
        after_result: Dict
    ) -> Dict:
        """Compare two benchmark results."""
        before_avg = before_result['timings']['average']
        after_avg = after_result['timings']['average']

        improvement_pct = ((before_avg - after_avg) / before_avg) * 100

        return {
            'before': before_result,
            'after': after_result,
            'comparison': {
                'average_improvement_ms': before_avg - after_avg,
                'average_improvement_pct': improvement_pct,
                'faster': improvement_pct > 0,
                'slower': improvement_pct < 0
            }
        }


class Reporter:
    """Format and display benchmark results."""

    @staticmethod
    def print_single_result(result: Dict, title: str = "Benchmark Results"):
        """Print a single benchmark result."""
        print("=" * 60)
        print(title.upper())
        print("=" * 60)
        print(f"Iterations: {result['iterations']:,}\n")

        print("TIMINGS:")
        print("-" * 60)
        timings = result['timings']
        print(f"  Average:  {timings['average']:.3f} ms")
        print(f"  Median:   {timings['median']:.3f} ms")
        print(f"  Min:      {timings['min']:.3f} ms")
        print(f"  Max:      {timings['max']:.3f} ms")
        print(f"  P95:      {timings['p95']:.3f} ms")
        print(f"  P99:      {timings['p99']:.3f} ms")

        print("\nMEMORY:")
        print("-" * 60)
        print(f"  Delta:    {result['memory']['deltaFormatted']}")
        print("=" * 60)

    @staticmethod
    def print_comparison(comparison: Dict):
        """Print comparison between before/after benchmarks."""
        before = comparison['before']
        after = comparison['after']
        comp = comparison['comparison']

        print("\n" + "=" * 60)
        print("BEFORE vs AFTER COMPARISON")
        print("=" * 60)

        print("\nBEFORE:")
        print("-" * 60)
        print(f"  Average:  {before['timings']['average']:.3f} ms")
        print(f"  P95:      {before['timings']['p95']:.3f} ms")

        print("\nAFTER:")
        print("-" * 60)
        print(f"  Average:  {after['timings']['average']:.3f} ms")
        print(f"  P95:      {after['timings']['p95']:.3f} ms")

        print("\nIMPROVEMENT:")
        print("-" * 60)

        if comp['faster']:
            icon = "🚀"
            verdict = "FASTER"
        elif comp['slower']:
            icon = "⚠️"
            verdict = "SLOWER"
        else:
            icon = "➡️"
            verdict = "NO CHANGE"

        print(f"{icon} {verdict}")
        print(f"  Average:  {comp['average_improvement_pct']:+.2f}%")
        print(f"  Absolute: {comp['average_improvement_ms']:+.3f} ms")
        print("=" * 60)

        if comp['slower']:
            print("\n⚠️  WARNING: Performance regression detected!")
            sys.exit(1)


def parse_function_spec(spec: str) -> tuple:
    """Parse 'file.ts:functionName' format."""
    parts = spec.split(':')
    if len(parts) != 2:
        print(f"Invalid function spec: {spec}", file=sys.stderr)
        print("Use format: file.ts:functionName", file=sys.stderr)
        sys.exit(1)
    return parts[0], parts[1]


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark JavaScript/TypeScript functions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Benchmark a single function
  python benchmark.py --file src/utils.ts --function sortArray --iterations 1000

  # Compare before/after optimization
  python benchmark.py \\
    --before src/old.ts:oldFunction \\
    --after src/new.ts:newFunction \\
    --iterations 5000

  # Output JSON for CI integration
  python benchmark.py --file src/utils.ts --function sortArray --format json
        """
    )

    parser.add_argument(
        '--file',
        type=str,
        help='File containing the function to benchmark'
    )

    parser.add_argument(
        '--function',
        type=str,
        help='Name of the function to benchmark'
    )

    parser.add_argument(
        '--before',
        type=str,
        help='Before optimization (format: file.ts:functionName)'
    )

    parser.add_argument(
        '--after',
        type=str,
        help='After optimization (format: file.ts:functionName)'
    )

    parser.add_argument(
        '--iterations',
        type=int,
        default=1000,
        help='Number of iterations to run (default: 1000)'
    )

    parser.add_argument(
        '--format',
        type=str,
        default='text',
        choices=['text', 'json'],
        help='Output format (default: text)'
    )

    args = parser.parse_args()

    runner = BenchmarkRunner()

    try:
        # Single benchmark mode
        if args.file and args.function:
            result = runner.run_benchmark(args.file, args.function, args.iterations)

            if args.format == 'json':
                print(json.dumps(result, indent=2))
            else:
                Reporter.print_single_result(result, f"{args.function} Benchmark")

        # Comparison mode
        elif args.before and args.after:
            before_file, before_fn = parse_function_spec(args.before)
            after_file, after_fn = parse_function_spec(args.after)

            print("Running BEFORE benchmark...")
            before_result = runner.run_benchmark(before_file, before_fn, args.iterations)

            print("Running AFTER benchmark...")
            after_result = runner.run_benchmark(after_file, after_fn, args.iterations)

            comparison = runner.compare_benchmarks(before_result, after_result)

            if args.format == 'json':
                print(json.dumps(comparison, indent=2))
            else:
                Reporter.print_comparison(comparison)

        else:
            parser.error("Either --file and --function OR --before and --after must be specified")

    finally:
        runner.cleanup()


if __name__ == '__main__':
    main()
