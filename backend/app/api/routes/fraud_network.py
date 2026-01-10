"""
Fraud Network Graph API - Real-time visualization of fraud connections

This innovative feature analyzes relationships between transactions to detect
fraud rings, patterns, and connected suspicious activities.

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ...db.database import get_db
from ...db.models import Prediction
from ...models.schemas import UserResponse
from ...services.auth_service import get_current_user

router = APIRouter(prefix="/fraud-network", tags=["Fraud Network"])


def calculate_similarity(pred1: Prediction, pred2: Prediction) -> Dict:
    """
    Calculate similarity between two predictions based on multiple factors.
    Returns similarity score and connection type.
    """
    connections = []
    total_score = 0

    # 1. Amount similarity (within 10% range)
    if pred1.amount > 0 and pred2.amount > 0:
        amount_diff = abs(pred1.amount - pred2.amount) / max(pred1.amount, pred2.amount)
        if amount_diff < 0.1:
            connections.append({
                "type": "similar_amount",
                "strength": 1 - amount_diff,
                "detail": f"${pred1.amount:.2f} ↔ ${pred2.amount:.2f}"
            })
            total_score += (1 - amount_diff) * 0.3

    # 2. Time proximity (within 1 hour)
    if pred1.created_at and pred2.created_at:
        time_diff = abs((pred1.created_at - pred2.created_at).total_seconds())
        if time_diff < 3600:  # 1 hour
            time_strength = 1 - (time_diff / 3600)
            connections.append({
                "type": "time_proximity",
                "strength": time_strength,
                "detail": f"{int(time_diff / 60)} min apart"
            })
            total_score += time_strength * 0.25

    # 3. Risk score similarity
    if pred1.risk_score and pred2.risk_score:
        risk_diff = abs(pred1.risk_score - pred2.risk_score) / 100
        if risk_diff < 0.15:
            risk_strength = 1 - risk_diff
            connections.append({
                "type": "similar_risk",
                "strength": risk_strength,
                "detail": f"Risk: {pred1.risk_score} ↔ {pred2.risk_score}"
            })
            total_score += risk_strength * 0.2

    # 4. Same batch (strong connection)
    if pred1.batch_id and pred2.batch_id and pred1.batch_id == pred2.batch_id:
        connections.append({
            "type": "same_batch",
            "strength": 1.0,
            "detail": f"Batch: {pred1.batch_id[:8]}"
        })
        total_score += 0.5

    # 5. Feature pattern similarity (using V features)
    if pred1.features_json and pred2.features_json:
        try:
            f1 = json.loads(pred1.features_json)
            f2 = json.loads(pred2.features_json)

            # Compare key V features (V1, V2, V3, V14, V17 - most important)
            key_features = ['v1', 'v2', 'v3', 'v14', 'v17']
            feature_similarity = 0
            count = 0

            for feat in key_features:
                if feat in f1 and feat in f2:
                    diff = abs(f1[feat] - f2[feat])
                    if diff < 1.0:  # Within 1 standard deviation
                        feature_similarity += 1 - diff
                        count += 1

            if count > 0:
                avg_similarity = feature_similarity / count
                if avg_similarity > 0.5:
                    connections.append({
                        "type": "feature_pattern",
                        "strength": avg_similarity,
                        "detail": f"Pattern match: {avg_similarity:.1%}"
                    })
                    total_score += avg_similarity * 0.25
        except:
            pass

    return {
        "score": min(total_score, 1.0),
        "connections": connections
    }


def detect_fraud_clusters(predictions: List[Prediction], threshold: float = 0.3) -> List[Dict]:
    """
    Detect clusters of related fraud predictions using similarity analysis.
    """
    if len(predictions) < 2:
        return []

    # Build adjacency list
    edges = []
    for i, pred1 in enumerate(predictions):
        for j, pred2 in enumerate(predictions[i+1:], i+1):
            similarity = calculate_similarity(pred1, pred2)
            if similarity["score"] >= threshold:
                edges.append({
                    "source": pred1.id,
                    "target": pred2.id,
                    "weight": similarity["score"],
                    "connections": similarity["connections"]
                })

    # Find connected components (clusters)
    if not edges:
        return []

    # Union-Find for clustering
    parent = {p.id: p.id for p in predictions}

    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for edge in edges:
        union(edge["source"], edge["target"])

    # Group by cluster
    clusters = defaultdict(list)
    for pred in predictions:
        clusters[find(pred.id)].append(pred.id)

    # Filter clusters with more than 1 member
    return [
        {"cluster_id": k, "members": v, "size": len(v)}
        for k, v in clusters.items()
        if len(v) > 1
    ]


@router.get(
    "/graph",
    summary="Get fraud network graph data",
    description="Returns nodes and edges for visualizing fraud connections."
)
async def get_fraud_network_graph(
    days: int = Query(7, ge=1, le=90, description="Days to analyze"),
    min_risk: int = Query(30, ge=0, le=100, description="Minimum risk score to include"),
    include_legitimate: bool = Query(False, description="Include legitimate transactions"),
    similarity_threshold: float = Query(0.25, ge=0.1, le=0.9, description="Connection threshold"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Generate fraud network graph data for visualization.

    Returns:
    - nodes: Transaction nodes with attributes
    - edges: Connections between similar transactions
    - clusters: Detected fraud rings/groups
    - statistics: Network analysis stats
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Query predictions
    query = db.query(Prediction).filter(
        Prediction.user_id == int(current_user.id),
        Prediction.created_at >= start_date,
        Prediction.risk_score >= min_risk
    )

    if not include_legitimate:
        query = query.filter(Prediction.is_fraud == True)

    predictions = query.order_by(Prediction.created_at.desc()).limit(200).all()

    if not predictions:
        return {
            "nodes": [],
            "edges": [],
            "clusters": [],
            "statistics": {
                "total_nodes": 0,
                "total_edges": 0,
                "clusters_found": 0,
                "density": 0
            }
        }

    # Build nodes
    nodes = []
    for pred in predictions:
        node = {
            "id": str(pred.id),
            "label": f"TX-{pred.id}",
            "amount": pred.amount,
            "risk_score": pred.risk_score,
            "is_fraud": pred.is_fraud,
            "fraud_probability": pred.fraud_probability,
            "confidence": pred.confidence,
            "created_at": pred.created_at.isoformat() if pred.created_at else None,
            "batch_id": pred.batch_id[:8] if pred.batch_id else None,
            # Node styling based on risk
            "size": 10 + (pred.risk_score / 10),  # Size by risk
            "color": get_node_color(pred.risk_score, pred.is_fraud)
        }
        nodes.append(node)

    # Build edges
    edges = []
    edge_id = 0
    for i, pred1 in enumerate(predictions):
        for pred2 in predictions[i+1:]:
            similarity = calculate_similarity(pred1, pred2)
            if similarity["score"] >= similarity_threshold:
                edge = {
                    "id": f"e{edge_id}",
                    "source": str(pred1.id),
                    "target": str(pred2.id),
                    "weight": similarity["score"],
                    "connections": similarity["connections"],
                    # Edge styling
                    "width": 1 + (similarity["score"] * 4),
                    "color": get_edge_color(similarity["score"]),
                    "label": f"{similarity['score']:.0%}"
                }
                edges.append(edge)
                edge_id += 1

    # Detect clusters
    clusters = detect_fraud_clusters(predictions, similarity_threshold)

    # Calculate statistics
    n_nodes = len(nodes)
    n_edges = len(edges)
    max_edges = n_nodes * (n_nodes - 1) / 2 if n_nodes > 1 else 1
    density = n_edges / max_edges if max_edges > 0 else 0

    # Find most connected nodes
    connection_count = defaultdict(int)
    for edge in edges:
        connection_count[edge["source"]] += 1
        connection_count[edge["target"]] += 1

    top_connected = sorted(
        connection_count.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    return {
        "nodes": nodes,
        "edges": edges,
        "clusters": clusters,
        "statistics": {
            "total_nodes": n_nodes,
            "total_edges": n_edges,
            "clusters_found": len(clusters),
            "density": round(density, 4),
            "avg_connections": round(n_edges * 2 / n_nodes, 2) if n_nodes > 0 else 0,
            "top_connected": [
                {"node_id": node_id, "connections": count}
                for node_id, count in top_connected
            ],
            "period_days": days,
            "min_risk_filter": min_risk
        }
    }


@router.get(
    "/node/{prediction_id}",
    summary="Get detailed node information",
    description="Get detailed information about a specific transaction node."
)
async def get_node_details(
    prediction_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get detailed information about a specific node including:
    - Full transaction details
    - All connected nodes
    - Connection explanations
    """
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == int(current_user.id)
    ).first()

    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    # Find connected predictions (same time window)
    time_window_start = prediction.created_at - timedelta(hours=24)
    time_window_end = prediction.created_at + timedelta(hours=24)

    related = db.query(Prediction).filter(
        Prediction.user_id == int(current_user.id),
        Prediction.id != prediction_id,
        Prediction.created_at >= time_window_start,
        Prediction.created_at <= time_window_end
    ).limit(50).all()

    connections = []
    for rel in related:
        similarity = calculate_similarity(prediction, rel)
        if similarity["score"] > 0.2:
            connections.append({
                "node_id": rel.id,
                "amount": rel.amount,
                "risk_score": rel.risk_score,
                "is_fraud": rel.is_fraud,
                "similarity_score": similarity["score"],
                "connection_types": similarity["connections"],
                "created_at": rel.created_at.isoformat() if rel.created_at else None
            })

    # Sort by similarity
    connections.sort(key=lambda x: x["similarity_score"], reverse=True)

    return {
        "node": {
            "id": prediction.id,
            "amount": prediction.amount,
            "risk_score": prediction.risk_score,
            "is_fraud": prediction.is_fraud,
            "fraud_probability": prediction.fraud_probability,
            "confidence": prediction.confidence,
            "prediction_time_ms": prediction.prediction_time_ms,
            "batch_id": prediction.batch_id,
            "created_at": prediction.created_at.isoformat() if prediction.created_at else None
        },
        "connections": connections[:20],
        "total_connections": len(connections)
    }


@router.get(
    "/clusters",
    summary="Get fraud clusters",
    description="Get detected fraud rings and clusters."
)
async def get_fraud_clusters(
    days: int = Query(7, ge=1, le=90),
    min_cluster_size: int = Query(2, ge=2, le=20),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Detect and return fraud clusters (potential fraud rings).
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    predictions = db.query(Prediction).filter(
        Prediction.user_id == int(current_user.id),
        Prediction.created_at >= start_date,
        Prediction.is_fraud == True
    ).order_by(Prediction.created_at.desc()).limit(100).all()

    clusters = detect_fraud_clusters(predictions, threshold=0.3)

    # Enrich cluster data
    enriched_clusters = []
    for cluster in clusters:
        if cluster["size"] >= min_cluster_size:
            members = []
            total_amount = 0
            avg_risk = 0

            for pred_id in cluster["members"]:
                pred = next((p for p in predictions if p.id == pred_id), None)
                if pred:
                    members.append({
                        "id": pred.id,
                        "amount": pred.amount,
                        "risk_score": pred.risk_score,
                        "created_at": pred.created_at.isoformat() if pred.created_at else None
                    })
                    total_amount += pred.amount
                    avg_risk += pred.risk_score

            enriched_clusters.append({
                "cluster_id": cluster["cluster_id"],
                "size": cluster["size"],
                "members": members,
                "total_amount": round(total_amount, 2),
                "avg_risk_score": round(avg_risk / cluster["size"], 1) if cluster["size"] > 0 else 0,
                "threat_level": "critical" if avg_risk / cluster["size"] > 75 else "high" if avg_risk / cluster["size"] > 50 else "medium"
            })

    # Sort by threat level
    enriched_clusters.sort(key=lambda x: x["avg_risk_score"], reverse=True)

    return {
        "clusters": enriched_clusters,
        "total_clusters": len(enriched_clusters),
        "total_fraud_in_clusters": sum(c["size"] for c in enriched_clusters),
        "period_days": days
    }


@router.get(
    "/timeline",
    summary="Get fraud activity timeline",
    description="Get fraud activity over time for animation."
)
async def get_fraud_timeline(
    days: int = Query(7, ge=1, le=30),
    interval: str = Query("hour", description="Interval: hour, day"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get fraud activity timeline for animated visualization.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    predictions = db.query(Prediction).filter(
        Prediction.user_id == int(current_user.id),
        Prediction.created_at >= start_date
    ).order_by(Prediction.created_at).all()

    timeline = []
    current_nodes = []

    for pred in predictions:
        event = {
            "timestamp": pred.created_at.isoformat() if pred.created_at else None,
            "type": "fraud" if pred.is_fraud else "legitimate",
            "node": {
                "id": str(pred.id),
                "amount": pred.amount,
                "risk_score": pred.risk_score,
                "is_fraud": pred.is_fraud
            }
        }
        timeline.append(event)

    return {
        "timeline": timeline,
        "total_events": len(timeline),
        "fraud_events": sum(1 for t in timeline if t["type"] == "fraud"),
        "period_days": days
    }


def get_node_color(risk_score: int, is_fraud: bool) -> str:
    """Get node color based on risk score and fraud status."""
    if is_fraud:
        if risk_score >= 75:
            return "#dc2626"  # Red - Critical
        elif risk_score >= 50:
            return "#ea580c"  # Orange - High
        else:
            return "#f59e0b"  # Amber - Medium
    else:
        if risk_score >= 50:
            return "#eab308"  # Yellow - Suspicious
        else:
            return "#22c55e"  # Green - Safe


def get_edge_color(weight: float) -> str:
    """Get edge color based on connection strength."""
    if weight >= 0.7:
        return "#dc2626"  # Strong connection - Red
    elif weight >= 0.5:
        return "#f97316"  # Medium - Orange
    elif weight >= 0.3:
        return "#eab308"  # Weak - Yellow
    else:
        return "#94a3b8"  # Very weak - Gray
