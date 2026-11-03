# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

def photo_service():
    from media import MediaService
    from repos import DonorRepo
    return ProfilePhoto(MediaService(), DonorRepo())

class ProfilePhoto:
    """A person's photo: one media id on their donor row. Replacing or removing it deletes the old file."""
    def __init__(self, media, donors): self.media, self.donors = media, donors

    def set(self, donor_id, upload):
        old = self.donors.by_id(donor_id)["photo_id"]
        new = self.media.save(upload, "avatar", donor_id)   # raises MediaRejected for anything that isn't a picture
        self.donors.set_column(donor_id, "photo_id", new)
        if old: self.media.delete(old)
        return new

    def remove(self, donor_id):
        old = self.donors.by_id(donor_id)["photo_id"]
        self.donors.set_column(donor_id, "photo_id", None)
        if old: self.media.delete(old)
