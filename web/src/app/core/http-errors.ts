import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';
export function errorMessage(error: HttpErrorResponse): string {
  const messages: Record<number, string> = {
    0: 'Le serveur est inaccessible. Vérifiez votre connexion.',
    400: 'La demande ne peut pas être traitée.',
    401: 'Votre session a expiré. Veuillez vous reconnecter.',
    403: 'Vous ne disposez pas des permissions nécessaires.',
    404: 'La ressource demandée est introuvable.',
    409: 'Cette opération entre en conflit avec l’état actuel de la ressource.',
    422: 'Les informations transmises sont invalides. Vérifiez les champs.',
    429: 'Trop de demandes. Réessayez dans quelques instants.',
    500: 'Une erreur est survenue sur le serveur.',
    503: 'Le service est temporairement indisponible.',
  };
  return messages[error.status] ?? 'Une erreur inattendue est survenue.';
}
export const errorInterceptor: HttpInterceptorFn = (request, next) =>
  next(request).pipe(
    catchError((error) =>
      throwError(
        () =>
          new Error(
            error instanceof HttpErrorResponse
              ? errorMessage(error)
              : 'Une erreur inattendue est survenue.',
          ),
      ),
    ),
  );
