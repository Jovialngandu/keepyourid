import { InjectionToken } from '@angular/core';
export interface RuntimeConfig {
  apiBaseUrl: string;
  workspaceEnabled: boolean;
}
export const CONFIG = new InjectionToken<RuntimeConfig>('runtime configuration');
