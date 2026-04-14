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
        'sprints/audit-s21',
      ],
    },
  ],

  algorithmsSidebar: [
    {
      type: 'category',
      label: 'Algorithmes',
      collapsed: false,
      items: [
        'algorithms/overview',
        'algorithms/pipeline',
        'algorithms/forecasting',
        'algorithms/analytics',
      ],
    },
  ],
};

export default sidebars;
