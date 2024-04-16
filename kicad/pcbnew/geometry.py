import kicad
import pcbnew
from typing import List
from kicad.point import Point
from kicad import SWIGtype

class Polygon(object):
    """Represents a polyline containing arcs as well as line segments: A chain of connected line and/or arc segments.

        This is a wrapper of pcbnew's SHAPE_LINE_CHAIN
    """
    def __init__(self, points: List[Point]) -> None:
        self._obj = SWIGtype.Polygon([pt.native_obj for pt in points])

    @property
    def native_obj(self):
        return self._obj

    @staticmethod
    def wrap(instance):
        return kicad.new(Polygon, instance)
    
    @property
    def points(self):
        return [Point.wrap(self.native_obj.CPoint(i).getWxPoint())
                for i in range(self.native_obj.PointCount())]


class PolygonSet(object):
    """Represents a set of polygons

        This is a wrapper of pcbnew's SHAPE_POLY_SET
    """
    def __init__(self, outline: Polygon = None) -> None:
        self._obj = SWIGtype.PolygonSet(outline and outline.native_obj)
        pass

    @property
    def native_obj(self):
        return self._obj

    @staticmethod
    def wrap(instance) -> 'PolygonSet':
        return kicad.new(PolygonSet, instance)
    
    @property
    def polygons(self) -> List[Polygon]:
        pass

    def add_polygon(self, polygon: Polygon):
        self._obj.AddOutline(polygon.native_obj)

    @property
    def area(self) -> float:
        return self._obj.Area()

    def difference(self, other: 'PolygonSet'):
        pass

    def intersection(self, other: 'PolygonSet', fast: bool = True):
        self._obj.BooleanIntersection(other.native_obj,
                                            pcbnew.SHAPE_POLY_SET.PM_FAST if fast else pcbnew.SHAPE_POLY_SET.PM_STRICTLY_SIMPLE)

    def union(self, other: 'PolygonSet'):
        pass

    def __iter__(self):
        for i in range(self._obj.OutlineCount()):
            yield Polygon.wrap(self._obj.Outline(i))
