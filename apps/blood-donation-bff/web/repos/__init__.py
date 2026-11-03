"""Repositories: the original interface, implemented over Nexus (reads: service state tables; writes: requests)."""
from ._nexus import RepoError
from .donors import DonorRepo, PermissionRepo, StaffRoleRepo
from .drives import DriveRepo, SlotRepo, InterestRepo
from .donations import DonationRepo, CertificateRepo, VoucherRepo, ReferralRepo, StatsRepo
from .tasks import TaskRepo, TaskEventRepo
from .donor_admin import DonorGridRepo, DonorGridQuery, SegmentRepo, ImportRepo
from .shared import MediaRepo, SocialPostRepo, ReportRepo, NotificationLogRepo, WidgetAccessRepo
