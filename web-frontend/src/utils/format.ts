import { format, formatDistanceToNow, isValid, parseISO } from 'date-fns';

export function formatDate(dateString: string, formatStr = 'PPP'): string {
  try {
    const date = parseISO(dateString);
    if (!isValid(date)) return 'Invalid date';
    return format(date, formatStr);
  } catch {
    return 'Invalid date';
  }
}

export function formatRelativeTime(dateString: string): string {
  try {
    const date = parseISO(dateString);
    if (!isValid(date)) return 'Unknown time';
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return 'Unknown time';
  }
}

export function formatPercentage(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  
  if (minutes < 60) {
    return remainingSeconds > 0 
      ? `${minutes}m ${remainingSeconds}s`
      : `${minutes}m`;
  }
  
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  
  return remainingMinutes > 0
    ? `${hours}h ${remainingMinutes}m`
    : `${hours}h`;
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

export function capitalizeFirst(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function formatConfidence(confidence: number): {
  value: string;
  color: string;
  label: string;
} {
  const percentage = Math.round(confidence * 100);
  
  let color: string;
  let label: string;
  
  if (percentage >= 90) {
    color = 'text-success-600';
    label = 'High';
  } else if (percentage >= 70) {
    color = 'text-warning-600';
    label = 'Medium';
  } else {
    color = 'text-error-600';
    label = 'Low';
  }
  
  return {
    value: `${percentage}%`,
    color,
    label
  };
}