from pydantic import BaseModel, Field
from typing import Optional
import uuid
from typing import ClassVar, List, Dict, Any, Iterator, Optional
from abc import ABC, abstractmethod


class OntologyEntity(BaseModel, ABC):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, description="The id of the entity")
    embedding: Optional[List[float]] = Field(None, description="The embedding vector.")

    @abstractmethod
    def __repr__(self):
        """Used for embedding"""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

class Mention(OntologyEntity):
    string: str = Field(..., description="The surface form of the mention")

    def __repr__(self):
        return self.string

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "string": self.string,
            "embedding": self.embedding,
        }


class FigureRef(OntologyEntity):
    label: str = Field(..., description="The label of the figure. E.g, Figure 1, etc.")
    caption: Optional[str] = Field(None, description="The caption of the figure")
    page_number: int = Field(..., description="The page number where the figure located. Use the page number information below the figues not above!")

    def __repr__(self):
        return f"{self.label} {self.caption}" if self.caption else self.label

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "caption": self.caption if self.caption else "",
            "page_number": self.page_number,
            "embedding": self.embedding,
        }


class Section(OntologyEntity):
    section_title: str = Field(..., description="The title of the section")
    summary: str = Field(..., description="The summary of the section, 150-200 words")
    content: str = Field(..., description="Full content of the section.")

    fig_refs: list[FigureRef] = Field(..., description="The list of all the figures are mentioned in the section.")
    mentions: list[Mention] = Field(..., description="The list of all entities appear in the section.")
    unit_title: Optional[str] = Field(None, description="The unit title of the section.")


    def __repr__(self):
        return f"{self.section_title} {self.summary}" + "\n" + "\n".join([repr(item) for item in self.fig_refs])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "section_title": self.section_title,
            "summary": self.summary,
            "content": self.content + "\nFigures: \n" + "\n".join([repr(item) for item in self.fig_refs]),
            "unit_title": self.unit_title,
            "embedding": self.embedding,
        }

class Unit(OntologyEntity):
    unit_title: str = Field(..., description="The title of the unit")
    summary: str = Field(..., description="The summary of the unit. 150-200 words")

    sections: list[Section] = Field(..., description="All the sections of the unit")

    def model_post_init(self, context: Any, /) -> None:
        for section in self.sections:
            section.unit_title = self.unit_title

    def __repr__(self):
        return f"{self.unit_title} {self.summary}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "unit_title": self.unit_title,
            "summary": self.summary,
            "embedding": self.embedding,
        }


class PageImage(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)

    page_number: int = Field(..., description="The page number of the page image")
    url: str = Field(..., description="The url of the page image")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "page_number": self.page_number,
            "url": self.url,
        }