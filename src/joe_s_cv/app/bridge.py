from PySide6.QtCore import QObject, Property, Slot, Signal
from pathlib import Path

from joe_s_cv.core.engine import ResumeFactory


class ResumeBridge(QObject):
    jobsChanged = Signal()
    statusChanged = Signal(str)

    def __init__(self):
        super().__init__()
        self.engine = ResumeFactory()
        self._status = "Ready"
        self._active_tabs = [
            {
                "company": "Radix",
                "title": "Robotics Engineer",
                "description": "Paste the requirements from LinkedIn/Indeed here...",
            }
        ]

    @Property(str, notify=statusChanged)
    def status(self):
        return self._status

    @Property("var", notify=jobsChanged)
    def activeTabs(self):
        return self._active_tabs

    @Slot(str)
    def processJob(self, job_name):
        self._status = f"Processing {job_name}..."
        self.statusChanged.emit(self._status)
        print(f"Engine logic triggered for: {job_name}")

    @Slot(int, str, str)
    def updateJobData(self, index, field, value):
        if 0 <= index < len(self._active_tabs):
            self._active_tabs[index][field] = value
            self.jobsChanged.emit()
            print(f"Updated {field} for job {index}: {value}")

    @Slot(int)
    def generateAI(self, index):
        if 0 <= index < len(self._active_tabs):
            job = self._active_tabs[index]
            print(f"AI generating for: {job['company']} - {job['title']}")
            self._status = f"AI generating for {job['title']}..."
            self.statusChanged.emit(self._status)

    @Slot(int)
    def duplicateJob(self, index):
        if 0 <= index < len(self._active_tabs):
            new_job = self._active_tabs[index].copy()
            new_job["title"] += " (Copy)"
            self._active_tabs.append(new_job)
            self.jobsChanged.emit()
            print(f"Duplicated job at index {index}")
