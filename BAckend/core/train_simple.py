#!/usr/bin/env python3
"""
Simple Aphasia Model - Minimal implementation for severity assessment
"""

import torch
import torch.nn as nn

class SimpleAphasiaModel(nn.Module):
    """Simple model for aphasia severity assessment."""
    
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(1, 64, kernel_size=80, stride=4)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=3)
        self.conv3 = nn.Conv1d(128, 256, kernel_size=3)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.fc1 = nn.Linear(256, 1)  # WAB-AQ score prediction
        self.fc2 = nn.Linear(256, 4)   # Severity classification
        
    def forward(self, x):
        # Ensure input has shape (batch, channels, length)
        if x.dim() == 1:
            x = x.unsqueeze(0).unsqueeze(0)
        elif x.dim() == 2:
            x = x.unsqueeze(1)

        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        x = torch.relu(self.conv3(x))
        x = self.pool(x).squeeze(-1)
        wab_aq = self.fc1(x).squeeze(-1)
        severity = self.fc2(x)
        return wab_aq, severity
