#!/bin/bash
cd /home/goyco/apps/jira-gpt
uvicorn main:app --host 0.0.0.0 --port 8090 --reload
