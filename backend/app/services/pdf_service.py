from datetime import datetime
from decimal import Decimal
from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from ..models.models import Producto
from ..repositories.product_repo import ProductRepository


class InventoryPdfService:
    def __init__(self, db: Session) -> None:
        self.product_repo = ProductRepository(db)

    def generate_inventory_pdf(
        self,
        username: str,
        generated_at: datetime,
    ) -> BytesIO:
        products = self.product_repo.get_all()
        document_buffer = BytesIO()
        document = SimpleDocTemplate(
            document_buffer,
            pagesize=landscape(A4),
            rightMargin=16 * mm,
            leftMargin=16 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title="Inventario de productos activos",
            author="Mini Mercadito",
            pageCompression=0,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "InventoryTitle",
            parent=styles["Title"],
            alignment=TA_LEFT,
            textColor=colors.HexColor("#24543a"),
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            spaceAfter=5,
        )
        metadata_style = ParagraphStyle(
            "InventoryMetadata",
            parent=styles["Normal"],
            textColor=colors.HexColor("#58665d"),
            fontSize=9,
            leading=13,
        )
        cell_style = ParagraphStyle(
            "InventoryCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
        )
        numeric_style = ParagraphStyle(
            "InventoryNumericCell",
            parent=cell_style,
            alignment=TA_RIGHT,
        )

        elements = [
            Paragraph("Mini Mercadito", title_style),
            Paragraph("Inventario de productos activos", styles["Heading2"]),
            Paragraph(
                f"Generado el {generated_at:%d/%m/%Y %H:%M} "
                f"por {escape(username)}",
                metadata_style,
            ),
            Spacer(1, 8 * mm),
        ]

        rows: list[list[object]] = [
            ["Producto", "Código de barras", "Precio", "Stock"]
        ]
        rows.extend(
            self._product_row(product, cell_style, numeric_style)
            for product in products
        )
        if not products:
            rows.append(
                [
                    Paragraph("No hay productos activos.", cell_style),
                    "",
                    "",
                    "",
                ],
            )

        table = Table(
            rows,
            colWidths=[105 * mm, 55 * mm, 35 * mm, 35 * mm],
            repeatRows=1,
            hAlign="LEFT",
        )
        table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24543a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [colors.white, colors.HexColor("#f1f5f1")],
            ),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dce5dc")),
        ]
        if not products:
            table_style.append(("SPAN", (0, 1), (-1, 1)))
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        document.build(elements)
        document_buffer.seek(0)
        return document_buffer

    @staticmethod
    def _product_row(
        product: Producto,
        cell_style: ParagraphStyle,
        numeric_style: ParagraphStyle,
    ) -> list[Paragraph]:
        return [
            Paragraph(escape(product.nombre), cell_style),
            Paragraph(escape(product.codigo_barras or "—"), cell_style),
            Paragraph(_format_currency(product.precio), numeric_style),
            Paragraph(str(product.stock_actual), numeric_style),
        ]


def _format_currency(amount: Decimal) -> str:
    formatted = (
        f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    return f"$ {formatted}"
