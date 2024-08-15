
from datetime import datetime, timezone

data['input'] = {
	"milli_datetime": datetime(year=2024, month=8, day=5, hour=18, minute=37, second=15, microsecond=455000),
	"sec_datetime": datetime(year=2024, month=8, day=5, hour=18, minute=37, second=15, tzinfo=timezone.utc),
	"formatted": datetime(year=2024, month=8, day=5)
}

