"""
Pydantic schemas for AG Grid related operations.
These schemas handle the request/response formats required by AG Grid.
"""
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class SortModel(BaseModel):
    """Schema for AG Grid sort model items."""
    colId: str
    sort: str  # 'asc' or 'desc'


class FilterModel(BaseModel):
    """Base schema for AG Grid filter models."""
    filterType: str


class TextFilterModel(FilterModel):
    """Schema for AG Grid text filters."""
    filterType: str = "text"
    type: str  # 'contains', 'equals', etc.
    filter: str


class NumberFilterModel(FilterModel):
    """Schema for AG Grid number filters."""
    filterType: str = "number"
    type: str  # 'equals', 'greaterThan', etc.
    filter: Union[int, float]


class DateFilterModel(FilterModel):
    """Schema for AG Grid date filters."""
    filterType: str = "date"
    type: str  # 'equals', 'greaterThan', etc.
    dateFrom: str
    dateTo: Optional[str] = None


class SetFilterModel(FilterModel):
    """Schema for AG Grid set filters."""
    filterType: str = "set"
    values: List[str]


class AgGridRequest(BaseModel):
    """
    Schema for AG Grid server-side row model requests.
    Handles pagination, filtering, and sorting.
    """
    startRow: int = Field(..., description="First row to fetch (0-based)")
    endRow: int = Field(..., description="Last row to fetch (exclusive)")
    rowGroupCols: List[Dict[str, Any]] = Field([], description="Columns to group by")
    valueCols: List[Dict[str, Any]] = Field([], description="Value columns for aggregation")
    pivotCols: List[Dict[str, Any]] = Field([], description="Columns to pivot by")
    pivotMode: bool = Field(False, description="Whether pivot mode is enabled")
    groupKeys: List[str] = Field([], description="Group keys for row groups")
    filterModel: Dict[str, Any] = Field({}, description="Filter model")
    sortModel: List[Dict[str, str]] = Field([], description="Sort model")


class AgGridResponse(BaseModel):
    """
    Schema for AG Grid server-side row model responses.
    Contains the row count and row data.
    """
    rowCount: int = Field(..., description="Total row count (before pagination)")
    rowData: List[Dict[str, Any]] = Field(..., description="Row data for the current page")
    
    @classmethod
    def create(cls, count: int, data: List[Dict[str, Any]]):
        """Helper method to create an AG Grid response."""
        return cls(rowCount=count, rowData=data)