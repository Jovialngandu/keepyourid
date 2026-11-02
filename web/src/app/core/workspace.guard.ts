import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { CONFIG } from './config';
// Local integration workspace only; this flag never authorizes backend operations.
export const workspaceGuard: CanActivateFn = () =>
  inject(CONFIG).workspaceEnabled || inject(Router).createUrlTree(['/login']);
