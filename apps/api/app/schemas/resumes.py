from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResumeExperience(BaseModel):
    company: str = ""
    title: str = ""
    start_date: str = ""
    end_date: str | None = None
    description: str = ""


class ResumeEducation(BaseModel):
    school: str = ""
    degree: str = ""
    major: str = ""
    start_date: str = ""
    end_date: str | None = None


class ResumeProject(BaseModel):
    name: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)


class ResumeSummary(BaseModel):
    name: str = ""
    email: str = ""
    phone: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[ResumeExperience] = Field(default_factory=list)
    education: list[ResumeEducation] = Field(default_factory=list)
    projects: list[ResumeProject] = Field(default_factory=list)
    follow_up_directions: list[str] = Field(default_factory=list)


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    status: str
    is_scanned: bool | None = None
    error_message: str | None = None
    summary: ResumeSummary | None = None
    created_at: datetime
    updated_at: datetime

