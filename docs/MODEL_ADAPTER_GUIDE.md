# Model Adapter Guide

This framework evaluates VO/VIO methods through command-line adapters.

## Required adapter behavior

Each adapter must:

1. Accept a dataset sequence path.
2. Accept an output trajectory path.
3. Run the VO/VIO method on the sequence.
4. Save the predicted trajectory at the requested output path.
5. Output trajectory in TUM format:

```text
timestamp tx ty tz qx qy qz qw
