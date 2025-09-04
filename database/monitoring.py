"""
Database Monitoring and Performance Tracking for MDUS System
Provides comprehensive monitoring, alerting, and performance analysis.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from contextlib import contextmanager

from sqlalchemy import text, func
from sqlalchemy.orm import Session

from .database import get_db_session

logger = logging.getLogger(__name__)


@dataclass
class QueryPerformanceMetric:
    """Query performance metric"""
    query: str
    total_time: float
    calls: int
    mean_time: float
    max_time: float
    min_time: float


@dataclass
class TableStatistic:
    """Table statistics"""
    table_name: str
    row_count: int
    table_size: int
    index_size: int
    total_size: int
    seq_scan: int
    seq_tup_read: int
    idx_scan: int
    idx_tup_fetch: int


class DatabaseMonitor:
    """Comprehensive database monitoring system"""
    
    def __init__(self):
        self.performance_history = []
        self.alert_thresholds = {
            'connection_pool_usage': 0.8,  # 80% pool utilization
            'long_running_query_seconds': 300,  # 5 minutes
            'lock_wait_seconds': 60,  # 1 minute
            'disk_usage_percentage': 85,  # 85% disk usage
            'cache_hit_ratio': 0.95,  # 95% cache hit ratio
            'index_hit_ratio': 0.95,  # 95% index hit ratio
        }
    
    def collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive database performance metrics"""
        try:
            with get_db_session() as session:
                metrics = {
                    'timestamp': datetime.utcnow(),
                    'connection_stats': self._get_connection_stats(session),
                    'query_performance': self._get_query_performance(session),
                    'table_statistics': self._get_table_statistics(session),
                    'index_statistics': self._get_index_statistics(session),
                    'cache_statistics': self._get_cache_statistics(session),
                    'lock_statistics': self._get_lock_statistics(session),
                    'disk_usage': self._get_disk_usage(session),
                    'replication_stats': self._get_replication_stats(session),
                }
                
                # Store in history for trend analysis
                self.performance_history.append(metrics)
                
                # Keep only last 24 hours of data
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                self.performance_history = [
                    m for m in self.performance_history 
                    if m['timestamp'] > cutoff_time
                ]
                
                return metrics
                
        except Exception as e:
            logger.error(f"Failed to collect performance metrics: {e}")
            return {'error': str(e), 'timestamp': datetime.utcnow()}
    
    def _get_connection_stats(self, session: Session) -> Dict[str, Any]:
        """Get database connection statistics"""
        try:
            stats = session.execute(text("""
                SELECT 
                    state,
                    COUNT(*) as count,
                    AVG(EXTRACT(EPOCH FROM (now() - state_change))) as avg_duration
                FROM pg_stat_activity 
                WHERE datname = current_database()
                GROUP BY state
            """)).fetchall()
            
            connection_stats = {row.state: {'count': row.count, 'avg_duration': row.avg_duration} 
                              for row in stats}
            
            # Get total connections
            total_connections = session.execute(text("""
                SELECT COUNT(*) FROM pg_stat_activity WHERE datname = current_database()
            """)).scalar()
            
            # Get max connections
            max_connections = session.execute(text("SHOW max_connections")).scalar()
            
            connection_stats['total_connections'] = total_connections
            connection_stats['max_connections'] = int(max_connections)
            connection_stats['utilization'] = total_connections / int(max_connections)
            
            return connection_stats
            
        except Exception as e:
            logger.error(f"Failed to get connection stats: {e}")
            return {'error': str(e)}
    
    def _get_query_performance(self, session: Session) -> Dict[str, Any]:
        """Get query performance statistics"""
        try:
            # Get top slow queries from pg_stat_statements
            slow_queries = session.execute(text("""
                SELECT 
                    LEFT(query, 100) as query_sample,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    max_exec_time,
                    min_exec_time,
                    rows,
                    shared_blks_hit,
                    shared_blks_read
                FROM pg_stat_statements 
                WHERE total_exec_time > 1000  -- Queries taking more than 1 second total
                ORDER BY total_exec_time DESC 
                LIMIT 10
            """)).fetchall()
            
            query_metrics = []
            for row in slow_queries:
                query_metrics.append(QueryPerformanceMetric(
                    query=row.query_sample,
                    total_time=row.total_exec_time,
                    calls=row.calls,
                    mean_time=row.mean_exec_time,
                    max_time=row.max_exec_time,
                    min_time=row.min_exec_time
                ).__dict__)
            
            # Get currently running slow queries
            active_queries = session.execute(text("""
                SELECT 
                    pid,
                    state,
                    LEFT(query, 100) as query_sample,
                    EXTRACT(EPOCH FROM (now() - query_start)) as duration
                FROM pg_stat_activity 
                WHERE state = 'active' 
                AND query NOT LIKE '%pg_stat_activity%'
                AND EXTRACT(EPOCH FROM (now() - query_start)) > 30
                ORDER BY duration DESC
            """)).fetchall()
            
            return {
                'slow_queries': query_metrics,
                'active_slow_queries': [dict(row) for row in active_queries],
                'total_queries_analyzed': len(slow_queries)
            }
            
        except Exception as e:
            logger.error(f"Failed to get query performance: {e}")
            return {'error': str(e)}
    
    def _get_table_statistics(self, session: Session) -> List[Dict[str, Any]]:
        """Get table usage statistics"""
        try:
            stats = session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_live_tup as row_count,
                    pg_total_relation_size(schemaname||'.'||tablename) as total_size,
                    pg_relation_size(schemaname||'.'||tablename) as table_size,
                    pg_indexes_size(schemaname||'.'||tablename) as index_size,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes
                FROM pg_stat_user_tables 
                JOIN pg_class ON pg_class.relname = tablename
                ORDER BY total_size DESC
            """)).fetchall()
            
            table_stats = []
            for row in stats:
                table_stats.append(TableStatistic(
                    table_name=f"{row.schemaname}.{row.tablename}",
                    row_count=row.row_count or 0,
                    table_size=row.table_size or 0,
                    index_size=row.index_size or 0,
                    total_size=row.total_size or 0,
                    seq_scan=row.seq_scan or 0,
                    seq_tup_read=row.seq_tup_read or 0,
                    idx_scan=row.idx_scan or 0,
                    idx_tup_fetch=row.idx_tup_fetch or 0
                ).__dict__)
            
            return table_stats
            
        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
            return [{'error': str(e)}]
    
    def _get_index_statistics(self, session: Session) -> Dict[str, Any]:
        """Get index usage statistics"""
        try:
            index_stats = session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan as scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched,
                    pg_relation_size(indexrelid) as size_bytes
                FROM pg_stat_user_indexes
                ORDER BY idx_scan DESC
            """)).fetchall()
            
            unused_indexes = session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    pg_relation_size(indexrelid) as size_bytes
                FROM pg_stat_user_indexes 
                WHERE idx_scan = 0 
                AND pg_relation_size(indexrelid) > 1024*1024  -- Larger than 1MB
                ORDER BY size_bytes DESC
            """)).fetchall()
            
            return {
                'index_usage': [dict(row) for row in index_stats],
                'unused_indexes': [dict(row) for row in unused_indexes],
                'total_indexes': len(index_stats)
            }
            
        except Exception as e:
            logger.error(f"Failed to get index statistics: {e}")
            return {'error': str(e)}
    
    def _get_cache_statistics(self, session: Session) -> Dict[str, Any]:
        """Get database cache statistics"""
        try:
            # Buffer cache hit ratio
            cache_stats = session.execute(text("""
                SELECT 
                    sum(heap_blks_read) as heap_read,
                    sum(heap_blks_hit) as heap_hit,
                    sum(heap_blks_read + heap_blks_hit) as heap_total,
                    CASE WHEN sum(heap_blks_read + heap_blks_hit) > 0 
                         THEN sum(heap_blks_hit) * 100.0 / sum(heap_blks_read + heap_blks_hit)
                         ELSE 0 
                    END as cache_hit_ratio
                FROM pg_statio_user_tables
            """)).fetchone()
            
            # Index cache hit ratio
            index_cache_stats = session.execute(text("""
                SELECT 
                    sum(idx_blks_read) as idx_read,
                    sum(idx_blks_hit) as idx_hit,
                    CASE WHEN sum(idx_blks_read + idx_blks_hit) > 0 
                         THEN sum(idx_blks_hit) * 100.0 / sum(idx_blks_read + idx_blks_hit)
                         ELSE 0 
                    END as index_hit_ratio
                FROM pg_statio_user_indexes
            """)).fetchone()
            
            # Shared buffer settings
            shared_buffers = session.execute(text("SHOW shared_buffers")).scalar()
            effective_cache_size = session.execute(text("SHOW effective_cache_size")).scalar()
            
            return {
                'heap_blocks_read': cache_stats.heap_read or 0,
                'heap_blocks_hit': cache_stats.heap_hit or 0,
                'cache_hit_ratio': float(cache_stats.cache_hit_ratio or 0),
                'index_hit_ratio': float(index_cache_stats.index_hit_ratio or 0),
                'shared_buffers': shared_buffers,
                'effective_cache_size': effective_cache_size
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache statistics: {e}")
            return {'error': str(e)}
    
    def _get_lock_statistics(self, session: Session) -> Dict[str, Any]:
        """Get database lock statistics"""
        try:
            locks = session.execute(text("""
                SELECT 
                    mode,
                    COUNT(*) as count
                FROM pg_locks 
                GROUP BY mode
                ORDER BY count DESC
            """)).fetchall()
            
            waiting_locks = session.execute(text("""
                SELECT 
                    l.pid,
                    l.mode,
                    l.locktype,
                    l.relation::regclass as relation,
                    a.query,
                    EXTRACT(EPOCH FROM (now() - a.query_start)) as wait_time
                FROM pg_locks l
                JOIN pg_stat_activity a ON l.pid = a.pid
                WHERE l.granted = false
                ORDER BY wait_time DESC
            """)).fetchall()
            
            blocking_queries = session.execute(text("""
                SELECT 
                    blocked_locks.pid AS blocked_pid,
                    blocked_activity.query as blocked_query,
                    blocking_locks.pid AS blocking_pid,
                    blocking_activity.query as blocking_query,
                    EXTRACT(EPOCH FROM (now() - blocked_activity.query_start)) as blocked_duration
                FROM pg_catalog.pg_locks blocked_locks
                JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
                JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
                    AND blocking_locks.relation = blocked_locks.relation
                    AND blocking_locks.page = blocked_locks.page
                    AND blocking_locks.tuple = blocked_locks.tuple
                    AND blocking_locks.virtualxid = blocked_locks.virtualxid
                    AND blocking_locks.transactionid = blocked_locks.transactionid
                    AND blocking_locks.classid = blocked_locks.classid
                    AND blocking_locks.objid = blocked_locks.objid
                    AND blocking_locks.objsubid = blocked_locks.objsubid
                    AND blocking_locks.pid != blocked_locks.pid
                JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
                WHERE NOT blocked_locks.granted
                ORDER BY blocked_duration DESC
            """)).fetchall()
            
            return {
                'lock_counts': [dict(row) for row in locks],
                'waiting_locks': [dict(row) for row in waiting_locks],
                'blocking_queries': [dict(row) for row in blocking_queries]
            }
            
        except Exception as e:
            logger.error(f"Failed to get lock statistics: {e}")
            return {'error': str(e)}
    
    def _get_disk_usage(self, session: Session) -> Dict[str, Any]:
        """Get database disk usage statistics"""
        try:
            # Database size
            db_size = session.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size,
                       pg_database_size(current_database()) as size_bytes
            """)).fetchone()
            
            # Tablespace usage
            tablespace_usage = session.execute(text("""
                SELECT 
                    spcname as tablespace,
                    pg_tablespace_location(oid) as location,
                    pg_size_pretty(pg_tablespace_size(spcname)) as size
                FROM pg_tablespace
            """)).fetchall()
            
            # Top 10 largest tables
            largest_tables = session.execute(text("""
                SELECT 
                    schemaname||'.'||tablename as table_name,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_stat_user_tables 
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10
            """)).fetchall()
            
            return {
                'database_size': db_size.size,
                'database_size_bytes': db_size.size_bytes,
                'tablespace_usage': [dict(row) for row in tablespace_usage],
                'largest_tables': [dict(row) for row in largest_tables]
            }
            
        except Exception as e:
            logger.error(f"Failed to get disk usage: {e}")
            return {'error': str(e)}
    
    def _get_replication_stats(self, session: Session) -> Dict[str, Any]:
        """Get replication statistics (if applicable)"""
        try:
            # Check if this is a primary server
            is_primary = session.execute(text("SELECT NOT pg_is_in_recovery()")).scalar()
            
            if is_primary:
                # Get replication slot information
                replication_slots = session.execute(text("""
                    SELECT 
                        slot_name,
                        plugin,
                        slot_type,
                        datoid,
                        active,
                        restart_lsn,
                        confirmed_flush_lsn
                    FROM pg_replication_slots
                """)).fetchall()
                
                # Get WAL sender information
                wal_senders = session.execute(text("""
                    SELECT 
                        pid,
                        state,
                        sent_lsn,
                        write_lsn,
                        flush_lsn,
                        replay_lsn,
                        write_lag,
                        flush_lag,
                        replay_lag
                    FROM pg_stat_replication
                """)).fetchall()
                
                return {
                    'is_primary': True,
                    'replication_slots': [dict(row) for row in replication_slots],
                    'wal_senders': [dict(row) for row in wal_senders]
                }
            else:
                # Get standby information
                recovery_info = session.execute(text("""
                    SELECT 
                        pg_last_wal_receive_lsn() as received_lsn,
                        pg_last_wal_replay_lsn() as replayed_lsn,
                        pg_last_xact_replay_timestamp() as last_replay_timestamp
                """)).fetchone()
                
                return {
                    'is_primary': False,
                    'recovery_info': dict(recovery_info) if recovery_info else {}
                }
                
        except Exception as e:
            logger.error(f"Failed to get replication stats: {e}")
            return {'is_primary': None, 'error': str(e)}
    
    def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for alert conditions based on thresholds"""
        alerts = []
        
        try:
            # Connection pool usage alert
            connection_stats = metrics.get('connection_stats', {})
            if connection_stats.get('utilization', 0) > self.alert_thresholds['connection_pool_usage']:
                alerts.append({
                    'severity': 'warning',
                    'type': 'connection_pool_high',
                    'message': f"Connection pool usage at {connection_stats['utilization']:.1%}",
                    'value': connection_stats['utilization']
                })
            
            # Long running queries alert
            query_perf = metrics.get('query_performance', {})
            long_queries = [q for q in query_perf.get('active_slow_queries', []) 
                          if q.get('duration', 0) > self.alert_thresholds['long_running_query_seconds']]
            if long_queries:
                alerts.append({
                    'severity': 'warning',
                    'type': 'long_running_queries',
                    'message': f"{len(long_queries)} queries running longer than {self.alert_thresholds['long_running_query_seconds']}s",
                    'queries': long_queries
                })
            
            # Lock wait alert
            lock_stats = metrics.get('lock_statistics', {})
            waiting_locks = [lock for lock in lock_stats.get('waiting_locks', [])
                           if lock.get('wait_time', 0) > self.alert_thresholds['lock_wait_seconds']]
            if waiting_locks:
                alerts.append({
                    'severity': 'critical',
                    'type': 'lock_wait_timeout',
                    'message': f"{len(waiting_locks)} locks waiting longer than {self.alert_thresholds['lock_wait_seconds']}s",
                    'locks': waiting_locks
                })
            
            # Cache hit ratio alert
            cache_stats = metrics.get('cache_statistics', {})
            cache_hit_ratio = cache_stats.get('cache_hit_ratio', 100) / 100
            if cache_hit_ratio < self.alert_thresholds['cache_hit_ratio']:
                alerts.append({
                    'severity': 'warning',
                    'type': 'low_cache_hit_ratio',
                    'message': f"Cache hit ratio at {cache_hit_ratio:.1%}",
                    'value': cache_hit_ratio
                })
            
            # Index hit ratio alert
            index_hit_ratio = cache_stats.get('index_hit_ratio', 100) / 100
            if index_hit_ratio < self.alert_thresholds['index_hit_ratio']:
                alerts.append({
                    'severity': 'warning',
                    'type': 'low_index_hit_ratio',
                    'message': f"Index hit ratio at {index_hit_ratio:.1%}",
                    'value': index_hit_ratio
                })
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
            alerts.append({
                'severity': 'error',
                'type': 'monitoring_error',
                'message': f"Failed to check some alert conditions: {str(e)}"
            })
        
        return alerts
    
    def get_performance_trends(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get performance trends over time"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        recent_metrics = [m for m in self.performance_history if m['timestamp'] > cutoff_time]
        
        if not recent_metrics:
            return {'error': 'No performance history available'}
        
        trends = {
            'timespan_hours': hours_back,
            'data_points': len(recent_metrics),
            'connection_utilization': [],
            'cache_hit_ratio': [],
            'active_queries': [],
            'database_size': []
        }
        
        for metric in recent_metrics:
            timestamp = metric['timestamp'].isoformat()
            
            # Connection utilization trend
            conn_util = metric.get('connection_stats', {}).get('utilization', 0)
            trends['connection_utilization'].append({
                'timestamp': timestamp,
                'value': conn_util
            })
            
            # Cache hit ratio trend
            cache_ratio = metric.get('cache_statistics', {}).get('cache_hit_ratio', 0)
            trends['cache_hit_ratio'].append({
                'timestamp': timestamp,
                'value': cache_ratio
            })
            
            # Active queries trend
            active_queries = len(metric.get('query_performance', {}).get('active_slow_queries', []))
            trends['active_queries'].append({
                'timestamp': timestamp,
                'value': active_queries
            })
            
            # Database size trend
            db_size = metric.get('disk_usage', {}).get('database_size_bytes', 0)
            trends['database_size'].append({
                'timestamp': timestamp,
                'value': db_size
            })
        
        return trends


# Global monitor instance
db_monitor = DatabaseMonitor()


@contextmanager
def query_timer():
    """Context manager for timing database queries"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        if duration > 1.0:  # Log queries taking more than 1 second
            logger.warning(f"Slow query detected: {duration:.2f}s")


def get_database_monitor() -> DatabaseMonitor:
    """Get global database monitor instance"""
    return db_monitor