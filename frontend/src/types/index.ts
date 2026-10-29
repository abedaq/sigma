export interface APIKeyConfig {
  id: string;
  name: string;
  provider: string;
  encrypted_key: string;
  masked_key: string;
  priority: number;
  status: string;
  quota_limit_rpm: number;
  current_rpm: number;
  remaining_quota_percent: number;
}

export interface JobProgress {
  job_id: string;
  file_name: string;
  stage: string;
  progress_percent: number;
  current_step_description: string;
  error_message?: string;
}

export interface SystemHardwareInfo {
  os_name: string;
  cpu_name: string;
  cpu_cores_physical: number;
  cpu_cores_logical: number;
  ram_total_gb: number;
  ram_available_gb: number;
  gpu_name: string;
  vram_total_gb: number;
  vram_available_gb: number;
  cuda_available: boolean;
  ffmpeg_version: string;
  python_version: string;
  app_version: string;
}
