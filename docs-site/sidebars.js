// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  guideSidebar: [
    {
      type: 'category',
      label: 'Guide',
      collapsed: false,
      items: [
        'guide/quickstart',
        'guide/installation',
        'guide/configuration',
      ],
    },
  ],

  architectureSidebar: [
    {
      type: 'category',
      label: 'Architecture',
      collapsed: false,
      items: [
        'architecture/overview',
        'architecture/ddd-hexagonal',
        'architecture/intelligence-module',
        'architecture/auth-flow',
        'architecture/forecasting-pipeline',
      ],
    },
  ],

  apiSidebar: [
    {
      type: 'category',
      label: 'API Reference',
      collapsed: false,
      items: [
        'api/graphql',
        'api/authentication',
        'api/inventory',
        'api/forecasting',
        'api/decisions',
      ],
    },
  ],

  sprintsSidebar: [
    {
      type: 'category',
      label: 'Sprints',
      collapsed: false,
      items: [
        'sprints/roadmap',
        'sprints/sprint-21',
      ],
    },
  ],
};

export default sidebars;
