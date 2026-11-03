# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

# One Excel/grid row uses exactly the same rules as every donor form (see validation/forms.py).
from validation.forms import DonorForm as DonorRow

__all__ = ["DonorRow"]
