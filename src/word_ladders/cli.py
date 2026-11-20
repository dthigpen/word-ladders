#!/usr/bin/env python3
"""
Unified CLI for word ladder toolkit.
"""

import argparse
import sys
from pathlib import Path

from word_ladders.lexicon import main as lexicon_main
from word_ladders.puzzles import main as puzzles_main
from word_ladders.thematic import main as thematic_main


def main():
    parser = argparse.ArgumentParser(
        description='Word Ladders Toolkit - Generate word lists and puzzles',
        prog='word-ladders'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Lexicon command
    lexicon_parser = subparsers.add_parser(
        'lexicon',
        help='Build the curated word list from raw dictionary'
    )
    lexicon_parser.add_argument(
        '-c', '--config',
        default='config/config.yaml',
        help='Path to config file'
    )
    
    # Puzzles command
    puzzles_parser = subparsers.add_parser(
        'puzzles',
        help='Generate random word ladder puzzles'
    )
    puzzles_parser.add_argument('-c', '--config', default='config/config.yaml', help='Path to config file')
    puzzles_parser.add_argument('-n', '--num-puzzles', type=int, help='Number of puzzles to generate')
    puzzles_parser.add_argument('--min-pqs', type=float, help='Minimum PQS threshold')
    puzzles_parser.add_argument('--min-distance', type=int, help='Minimum intermediate steps')
    puzzles_parser.add_argument('--max-distance', type=int, help='Maximum intermediate steps')
    puzzles_parser.add_argument('-w', '--word-list', help='Path to word list')
    puzzles_parser.add_argument('-o', '--output', help='Output file path')
    puzzles_parser.add_argument('--seed', type=int, help='Random seed for deterministic generation')
    puzzles_parser.add_argument('--easy', type=int, help='Target count for Easy puzzles')
    puzzles_parser.add_argument('--medium', type=int, help='Target count for Medium puzzles')
    puzzles_parser.add_argument('--hard', type=int, help='Target count for Hard puzzles')
    puzzles_parser.add_argument('--expert', type=int, help='Target count for Expert puzzles')
    puzzles_parser.add_argument('--solve', nargs=2, metavar=('START', 'END'), help='Solve a specific word ladder pair')
    puzzles_parser.add_argument('--include-thematic', action='store_true', help='Include thematic puzzles in output')
    puzzles_parser.add_argument('--thematic-only', action='store_true', help='Generate only thematic puzzles')
    
    # Thematic command
    thematic_parser = subparsers.add_parser(
        'thematic',
        help='Generate thematic word ladder puzzles'
    )
    thematic_parser.add_argument('-c', '--config', default='config/config.yaml', help='Path to config file')
    thematic_parser.add_argument('-w', '--word-list', help='Path to word list')
    thematic_parser.add_argument('-o', '--output', help='Output file path')
    thematic_parser.add_argument('--min-pqs', type=float, help='Minimum PQS threshold')
    thematic_parser.add_argument('--min-distance', type=int, help='Minimum intermediate steps')
    thematic_parser.add_argument('--max-distance', type=int, help='Maximum intermediate steps')
    thematic_parser.add_argument('--max-per-domain', type=int, help='Max pairs per domain pair')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Route to appropriate command
    if args.command == 'lexicon':
        # Build custom argv for the subcommand
        sys.argv = ['lexicon']
        if args.config:
            sys.argv.extend(['-c', args.config])
        lexicon_main()
    elif args.command == 'puzzles':
        # Build custom argv for the subcommand
        sys.argv = ['puzzles']
        if args.config:
            sys.argv.extend(['-c', args.config])
        if args.num_puzzles:
            sys.argv.extend(['-n', str(args.num_puzzles)])
        if args.min_pqs:
            sys.argv.extend(['--min-pqs', str(args.min_pqs)])
        if args.min_distance:
            sys.argv.extend(['--min-distance', str(args.min_distance)])
        if args.max_distance:
            sys.argv.extend(['--max-distance', str(args.max_distance)])
        if args.word_list:
            sys.argv.extend(['-w', args.word_list])
        if args.output:
            sys.argv.extend(['-o', args.output])
        if args.seed:
            sys.argv.extend(['--seed', str(args.seed)])
        if args.easy:
            sys.argv.extend(['--easy', str(args.easy)])
        if args.medium:
            sys.argv.extend(['--medium', str(args.medium)])
        if args.hard:
            sys.argv.extend(['--hard', str(args.hard)])
        if args.expert:
            sys.argv.extend(['--expert', str(args.expert)])
        if args.solve:
            sys.argv.extend(['--solve'] + args.solve)
        if args.include_thematic:
            sys.argv.extend(['--include-thematic'])
        if args.thematic_only:
            sys.argv.extend(['--thematic-only'])
        puzzles_main()
    elif args.command == 'thematic':
        # Build custom argv for the subcommand
        sys.argv = ['thematic']
        if args.config:
            sys.argv.extend(['-c', args.config])
        if args.word_list:
            sys.argv.extend(['-w', args.word_list])
        if args.output:
            sys.argv.extend(['-o', args.output])
        if args.min_pqs:
            sys.argv.extend(['--min-pqs', str(args.min_pqs)])
        if args.min_distance:
            sys.argv.extend(['--min-distance', str(args.min_distance)])
        if args.max_distance:
            sys.argv.extend(['--max-distance', str(args.max_distance)])
        if args.max_per_domain:
            sys.argv.extend(['--max-per-domain', str(args.max_per_domain)])
        thematic_main()


if __name__ == '__main__':
    main()
