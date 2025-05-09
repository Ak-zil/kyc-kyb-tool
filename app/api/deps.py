"""
API dependencies for FastAPI.
Contains dependency injection functions for API endpoints.
"""
from typing import Generator, Dict, Any, Optional, List

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ag_grid import AgGridRequest


def get_ag_grid_params(
    startRow: int = Query(0, description="First row to fetch (0-based)"),
    endRow: int = Query(100, description="Last row to fetch (exclusive)"),
    filterModel: Optional[Dict[str, Any]] = Query({}, description="Filter model"),
    sortModel: Optional[List[Dict[str, str]]] = Query([], description="Sort model")
) -> AgGridRequest:
    """
    Dependency to parse AG Grid request parameters.
    Handles pagination, filtering, and sorting.
    
    Args:
        startRow (int): First row to fetch (0-based)
        endRow (int): Last row to fetch (exclusive)
        filterModel (Dict): Filter model from AG Grid
        sortModel (List[Dict]): Sort model from AG Grid
        
    Returns:
        AgGridRequest: Parsed AG Grid request
    """
    return AgGridRequest(
        startRow=startRow,
        endRow=endRow,
        rowGroupCols=[],
        valueCols=[],
        pivotCols=[],
        pivotMode=False,
        groupKeys=[],
        filterModel=filterModel or {},
        sortModel=sortModel or []
    )


# Common dependencies
db_dependency = Depends(get_db)
ag_grid_dependency = Depends(get_ag_grid_params)