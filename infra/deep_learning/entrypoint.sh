#!/bin/bash

# Clone current status of project repository
git clone https://hannesk95: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@github.com/semester-project/TUM-DI-LAB.git
cd /workspace/TUM-DI-LAB
git checkout dev
cd /workspace

cd /workspace/mount_dir/
mlflow ui -h 0.0.0.0 -p 5000 &
cd /workspace

# Start bash
/bin/bash