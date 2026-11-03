# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from .charts import DonationsTrend, BloodGroups, DriveFunnel, UpcomingFill, TaskStatus, ChannelDelivery
from .cards import ImpactStats, TopDonors, TopRecruiters, TaskLifecycle

WIDGET_CLASSES = (ImpactStats, DonationsTrend, BloodGroups, DriveFunnel, UpcomingFill, TaskStatus,
                  TopDonors, TopRecruiters, TaskLifecycle, ChannelDelivery)
