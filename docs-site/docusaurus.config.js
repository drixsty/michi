// @ts-check
import {themes as prismThemes} from 'prism-react-renderer';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Michi 道',
  tagline: 'Plateforme SaaS de prévision de stocks omnicanale',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://docs.michi.app',
  baseUrl: '/',

  organizationName: 'michi-app',
  projectName: 'michi',

  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'fr',
    locales: ['fr', 'en'],
  },

  stylesheets: [
    {
      href: 'https://cdn.jsdelivr.net/npm/katex@0.13.24/dist/katex.min.css',
      type: 'text/css',
      integrity:
        'sha384-odtC+0UGzzFL/6PNoE8rX/SPcQDXBJ+uRepguP4QkPCm7KGKu8GRRG2LXOc7u9Pb',
      crossorigin: 'anonymous',
    },
  ],

  markdown: {
    mermaid: true,
  },
  themes: ['@docusaurus/theme-mermaid'],

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          routeBasePath: '/',
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      colorMode: {
        defaultMode: 'light',
        respectPrefersColorScheme: true,
      },
      navbar: {
        title: 'Michi 道',
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'guideSidebar',
            position: 'left',
            label: 'Guide',
          },
          {
            type: 'docSidebar',
            sidebarId: 'architectureSidebar',
            position: 'left',
            label: 'Architecture',
          },
          {
            type: 'docSidebar',
            sidebarId: 'apiSidebar',
            position: 'left',
            label: 'API',
          },
          {
            type: 'docSidebar',
            sidebarId: 'sprintsSidebar',
            position: 'left',
            label: 'Sprints',
          },
          {
            href: 'https://github.com/michi-app/michi',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Documentation',
            items: [
              {label: 'Quickstart', to: '/guide/quickstart'},
              {label: 'Architecture DDD', to: '/architecture/overview'},
              {label: 'API Reference', to: '/api/graphql'},
            ],
          },
          {
            title: 'Sprints',
            items: [
              {label: 'Sprint 21 — DDD Hexagonal', to: '/sprints/sprint-21'},
              {label: 'Roadmap', to: '/sprints/roadmap'},
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Michi 道. Propulsé par Docusaurus.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
        additionalLanguages: ['python', 'bash', 'graphql', 'typescript'],
      },
    }),
};

export default config;
