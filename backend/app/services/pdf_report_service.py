"""Enhanced PDF report generation with charts and analytics"""

import io
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PDFReportService:
    """
    Advanced PDF report generation service

    Features:
    - Transaction history reports
    - Fraud analytics with charts
    - Performance metrics
    - Custom branded reports
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=12,
            spaceBefore=12
        ))

    def _create_header(self) -> List:
        """Create report header"""
        elements = []

        title = Paragraph("Fraud Detection System - Analytics Report", self.styles['CustomTitle'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))

        # Report metadata
        metadata = [
            ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Report Type:", "Comprehensive Analytics"],
        ]

        meta_table = Table(metadata, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        elements.append(meta_table)
        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _create_summary_table(self, stats: Dict[str, Any]) -> Table:
        """Create summary statistics table"""
        data = [
            ['Metric', 'Value'],
            ['Total Transactions', str(stats.get('total_predictions', 0))],
            ['Fraud Detected', str(stats.get('fraud_count', 0))],
            ['Fraud Rate', f"{stats.get('fraud_rate', 0):.2%}"],
            ['Avg Risk Score', f"{stats.get('avg_risk_score', 0):.1f}"],
            ['High Risk Transactions', str(stats.get('high_risk_count', 0))],
        ]

        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))

        return table

    def _create_fraud_chart(self, fraud_data: Dict[str, int]) -> Optional[Image]:
        """Create fraud statistics pie chart"""
        try:
            fig, ax = plt.subplots(figsize=(6, 4))

            labels = list(fraud_data.keys())
            sizes = list(fraud_data.values())
            colors_list = ['#22c55e', '#ef4444']

            ax.pie(sizes, labels=labels, colors=colors_list, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            ax.set_title('Fraud vs Legitimate Transactions')

            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            buf.seek(0)

            # Create ReportLab image
            img = Image(buf, width=4*inch, height=3*inch)
            return img

        except Exception as e:
            logger.error(f"Failed to create chart: {e}")
            return None

    def _create_timeline_chart(self, timeline_data: List[Dict]) -> Optional[Image]:
        """Create fraud detection timeline chart"""
        try:
            if not timeline_data:
                return None

            fig, ax = plt.subplots(figsize=(8, 4))

            dates = [d['date'] for d in timeline_data]
            fraud_counts = [d['fraud_count'] for d in timeline_data]
            total_counts = [d['total_count'] for d in timeline_data]

            ax.plot(dates, fraud_counts, marker='o', color='#ef4444', label='Fraud', linewidth=2)
            ax.plot(dates, total_counts, marker='s', color='#3b82f6', label='Total', linewidth=2)

            ax.set_xlabel('Date')
            ax.set_ylabel('Transaction Count')
            ax.set_title('Transaction Timeline')
            ax.legend()
            ax.grid(True, alpha=0.3)

            plt.xticks(rotation=45)

            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            buf.seek(0)

            img = Image(buf, width=6*inch, height=3*inch)
            return img

        except Exception as e:
            logger.error(f"Failed to create timeline chart: {e}")
            return None

    def _create_transaction_table(self, transactions: List[Dict]) -> Table:
        """Create detailed transaction table"""
        data = [['Date', 'Amount', 'Risk Score', 'Status']]

        for txn in transactions[:20]:  # Limit to 20
            data.append([
                txn.get('date', 'N/A'),
                f"${txn.get('amount', 0):.2f}",
                f"{txn.get('risk_score', 0):.1f}",
                '🚨 Fraud' if txn.get('is_fraud') else '✓ Safe'
            ])

        table = Table(data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))

        return table

    def generate_analytics_report(
        self,
        db: Session,
        user_id: int,
        days: int = 30
    ) -> bytes:
        """
        Generate comprehensive analytics PDF report

        Args:
            db: Database session
            user_id: User ID
            days: Number of days to include

        Returns:
            PDF bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)

        elements = []

        # Header
        elements.extend(self._create_header())

        # Executive Summary
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.1*inch))

        # Get statistics (mock data for now - integrate with real DB)
        stats = {
            'total_predictions': 1250,
            'fraud_count': 45,
            'fraud_rate': 0.036,
            'avg_risk_score': 23.5,
            'high_risk_count': 78
        }

        elements.append(self._create_summary_table(stats))
        elements.append(Spacer(1, 0.3*inch))

        # Fraud Distribution Chart
        elements.append(Paragraph("Fraud Distribution", self.styles['SectionHeader']))
        fraud_chart = self._create_fraud_chart({
            'Legitimate': stats['total_predictions'] - stats['fraud_count'],
            'Fraud': stats['fraud_count']
        })
        if fraud_chart:
            elements.append(fraud_chart)
        elements.append(Spacer(1, 0.2*inch))

        # Page break before timeline
        elements.append(PageBreak())

        # Timeline Chart
        elements.append(Paragraph("Transaction Timeline", self.styles['SectionHeader']))
        timeline_data = [
            {'date': 'Day 1', 'fraud_count': 2, 'total_count': 42},
            {'date': 'Day 2', 'fraud_count': 1, 'total_count': 38},
            {'date': 'Day 3', 'fraud_count': 3, 'total_count': 45},
            {'date': 'Day 4', 'fraud_count': 1, 'total_count': 40},
            {'date': 'Day 5', 'fraud_count': 2, 'total_count': 43},
        ]
        timeline_chart = self._create_timeline_chart(timeline_data)
        if timeline_chart:
            elements.append(timeline_chart)
        elements.append(Spacer(1, 0.3*inch))

        # Recent Transactions
        elements.append(Paragraph("Recent Transactions", self.styles['SectionHeader']))
        transactions = [
            {'date': '2026-01-08', 'amount': 150.50, 'risk_score': 25.3, 'is_fraud': False},
            {'date': '2026-01-08', 'amount': 1250.00, 'risk_score': 85.7, 'is_fraud': True},
            {'date': '2026-01-07', 'amount': 45.20, 'risk_score': 12.1, 'is_fraud': False},
        ]
        elements.append(self._create_transaction_table(transactions))

        # Build PDF
        doc.build(elements)

        buffer.seek(0)
        return buffer.getvalue()

    def generate_simple_report(
        self,
        transactions: List[Dict],
        title: str = "Transaction Report"
    ) -> bytes:
        """Generate a simple transaction report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)

        elements = []

        # Title
        elements.append(Paragraph(title, self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.3*inch))

        # Table
        if transactions:
            elements.append(self._create_transaction_table(transactions))
        else:
            elements.append(Paragraph("No transactions found.", self.styles['Normal']))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


pdf_service = PDFReportService()
