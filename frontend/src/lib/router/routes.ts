export type AppRoute =
  | {
      name: 'docs';
      docId?: string;
    }
  | {
      name: 'report';
    };

export type AppRouteName = AppRoute['name'];

export type PrimaryRoute = {
  name: AppRouteName;
  label: string;
  href: string;
};

const defaultRoute: AppRoute = { name: 'docs' };

export const primaryRoutes: PrimaryRoute[] = [
  {
    name: 'docs',
    label: 'Docs',
    href: routeHref({ name: 'docs' }),
  },
  {
    name: 'report',
    label: 'Report',
    href: routeHref({ name: 'report' }),
  },
];

export function parseRoute(hash: string): AppRoute {
  const path = hash.replace(/^#\/?/, '').replace(/^\//, '');
  if (!path) return defaultRoute;

  const [section, ...rest] = path.split('/');

  if (section === 'report') {
    return { name: 'report' };
  }

  if (section === 'docs') {
    return {
      name: 'docs',
      docId: rest.join('/') || undefined,
    };
  }

  return defaultRoute;
}

export function routeHref(route: AppRoute): string {
  if (route.name === 'report') return '#/report';
  if (route.docId) return `#/docs/${route.docId}`;
  return '#/docs';
}
