import { ResearchProject, Collection } from '../types';

export const INITIAL_PROJECTS: ResearchProject[] = [
  {
    id: 'quantum-2024',
    title: 'Advancements in Quantum Computing: 2024 Analysis',
    description: 'Detailed breakdown of error correction, surface codes, and modular QPU scalability.',
    query: 'Provide a detailed analysis of Quantum Computing Advancements in 2024, focusing on error correction and scalability. Include references to major institutional breakthroughs.',
    mode: 'deep',
    createdAt: '2026-07-28T10:00:00Z',
    updatedAt: '2026-07-28T11:30:00Z',
    dateLabel: 'Oct 28',
    status: 'completed',
    category: 'Quantum Computing',
    isStarred: true,
    isShared: false,
    messages: [
      {
        id: 'msg-1-u',
        role: 'user',
        content: 'Provide a detailed analysis of Quantum Computing Advancements in 2024, focusing on error correction and scalability. Include references to major institutional breakthroughs.',
        timestamp: '10:00 AM'
      },
      {
        id: 'msg-1-a',
        role: 'assistant',
        title: 'Advancements in Quantum Computing: 2024 Analysis',
        content: 'The landscape of quantum computing in 2024 has transitioned from theoretical viability to practical engineering challenges, specifically targeting logical qubit stability and fault-tolerant architectures. The focus has demonstrably shifted from simply increasing raw physical qubit counts to enhancing error mitigation and achieving scalable logical qubits.',
        citations: [1, 2, 3],
        timestamp: '10:01 AM',
        sections: [
          {
            heading: 'Breakthroughs in Error Correction',
            body: 'Significant progress has been made in dynamic logical qubits. Traditional surface code approaches have been augmented with machine learning-driven decoding algorithms, drastically reducing the overhead required for error correction.',
            bulletPoints: [
              'Logical Qubit Fidelity: Several labs reported achieving logical error rates lower than their constituent physical error rates, crossing the critical breakeven point.',
              'Real-time Decoding: Implementation of ASIC-based decoders has enabled real-time error tracking, essential for deep quantum circuits.'
            ]
          },
          {
            heading: 'Scalability and Hardware Architecture',
            body: 'Modular architectures have emerged as the primary paradigm for scaling. Instead of monolithic chips, institutions are linking multiple smaller QPU (Quantum Processing Unit) modules via high-fidelity quantum interconnects.'
          }
        ],
        codeSnippet: `// Example of logical qubit instantiation paradigm
QubitRegistry.Initialize(module_id: 4, logical_qubits: 12)
ErrorCorrection.BindSurfaceCode(distance: 5, cycle_time: 1ns)
Link.EstablishEntanglement(source_module: 4, target_module: 5, fidelity_threshold: 0.999)`
      }
    ],
    sources: [
      {
        id: 'src-1',
        index: 1,
        title: 'Beyond Breakeven: Fault-Tolerant Logical Qubits in Superconducting Processors',
        authors: 'Smith, J., Doe, A. et al.',
        year: 2024,
        journal: 'Nature Physics, Vol. 20, Feb 2024.',
        relevance: 0.98,
        doi: '10.1038/s41558-024-0012',
        url: 'https://doi.org/10.1038/s41558-024-0012',
        tags: ['Peer Reviewed', 'PDF Available'],
        abstract: 'Demonstration of fault-tolerant logical qubits operating below physical breakeven thresholds using 2D superconducting circuit lattices.'
      },
      {
        id: 'src-2',
        index: 2,
        title: 'Real-time Decoding of Surface Codes via ASIC Architecture',
        authors: 'Patel, R., Tanaka, H.',
        year: 2024,
        journal: 'IEEE Transactions on Quantum Engineering, Mar 2024.',
        relevance: 0.92,
        doi: '10.1109/TQE.2024.33120',
        url: 'https://doi.org/10.1109/TQE.2024.33120',
        tags: ['Technical Report'],
        abstract: 'Custom ASIC design achieving sub-microsecond syndrome decoding for real-time quantum error correction loops.'
      },
      {
        id: 'src-3',
        index: 3,
        title: 'Modular Scaling Paradigms for Next-Generation QPU Arrays',
        authors: 'MIT Quantum Lab Research Consortium',
        year: 2024,
        journal: 'MIT Quantum Lab Pre-prints, Jan 2024.',
        relevance: 0.89,
        doi: '10.48550/arXiv.2401.09912',
        url: 'https://arxiv.org/abs/2401.09912',
        tags: ['Pre-print', 'Institution Data'],
        abstract: 'A distributed QPU network model utilizing optical quantum links to achieve high entanglement rates across modular chip sets.'
      }
    ],
    attachedFiles: []
  },
  {
    id: 'climate-alpha',
    title: 'Project Alpha: Climate Synthesis',
    description: 'A compiled list of peer-reviewed sources on anthropogenic aerosols, methane emissions, and ocean acidification.',
    query: 'Synthesize current literature on anthropogenic aerosols, methane emissions from permafrost, and marine ecosystem impacts.',
    mode: 'deep',
    createdAt: '2026-07-25T14:00:00Z',
    updatedAt: '2026-07-27T09:12:00Z',
    dateLabel: 'Oct 27',
    status: 'completed',
    category: 'Climate Science',
    isStarred: true,
    isShared: true,
    messages: [
      {
        id: 'msg-clim-1',
        role: 'user',
        content: 'Synthesize current literature on anthropogenic aerosols, methane emissions from permafrost, and marine ecosystem impacts.',
        timestamp: '2:00 PM'
      },
      {
        id: 'msg-clim-2',
        role: 'assistant',
        title: 'Project Alpha: Climate Synthesis Report',
        content: 'Climate models in recent literature demonstrate significant radiative forcing interplay between aerosol cooling and Arctic feedback mechanisms. Methane emissions from degraded permafrost accelerate thermal amplification in high latitude zones.',
        citations: [1, 2, 3],
        timestamp: '2:02 PM',
        sections: [
          {
            heading: 'Anthropogenic Aerosol Radiative Forcing',
            body: 'Aerosol-cloud interactions account for substantial uncertainty in net surface temperature projections. High-density satellite observations confirm localized cooling trends counteracting greenhouse forcing.'
          },
          {
            heading: 'Permafrost Degradation Dynamics',
            body: 'Thermokarst lakes in sub-Arctic Russia and North America are emitting higher-than-predicted biogenic methane spikes during spring thaws.'
          }
        ]
      }
    ],
    sources: [
      {
        id: 'src-c1',
        index: 1,
        title: 'Long-term effects of anthropogenic aerosols on global temperature patterns',
        authors: 'Smith, J., Doe, A.',
        year: 2023,
        journal: 'Nature Climate Change',
        relevance: 0.98,
        doi: '10.1038/s41558',
        url: 'https://doi.org/10.1038/s41558',
        tags: ['DOI: 10.1038/s41558', 'PDF Available'],
        abstract: 'Evaluation of historical cloud condensate data showing a -1.1 W/m2 cooling offset from sulfate particulates.'
      },
      {
        id: 'src-c2',
        index: 2,
        title: 'Methane emissions from arctic permafrost degradation in the 21st century',
        authors: 'Johnson, M. et al.',
        year: 2022,
        journal: 'Science Advances',
        relevance: 0.95,
        doi: '10.1126/sciadv',
        url: 'https://doi.org/10.1126/sciadv',
        tags: ['DOI: 10.1126/sciadv', 'Local Copy'],
        abstract: 'Field flux tower measurements across Alaska and Siberia quantifying methane release rates under elevated temperature scenarios.'
      },
      {
        id: 'src-c3',
        index: 3,
        title: 'Ocean acidification and its impact on calcifying marine organisms',
        authors: 'Lee, C., Wong, H.',
        year: 2024,
        journal: 'Global Change Biology',
        relevance: 0.89,
        doi: '10.1111/gcb',
        url: 'https://doi.org/10.1111/gcb',
        tags: ['DOI: 10.1111/gcb'],
        abstract: 'Meta-analysis of 140 experimental trials analyzing aragonite saturation horizons and larval bivalve shell dissolution.'
      },
      {
        id: 'src-c4',
        index: 4,
        title: 'Stratospheric aerosol injection modeling under regional climate pathways',
        authors: 'Garrido, F., Vane, E.',
        year: 2023,
        journal: 'Journal of Geophysical Research',
        relevance: 0.85,
        doi: '10.1029/jgr.2023',
        tags: ['DOI: 10.1029/jgr'],
        abstract: 'Solar radiation management simulation indicating precipitation shifts in tropical regions during high sulfur loading.'
      }
    ],
    attachedFiles: []
  },
  {
    id: 'solid-state-batteries',
    title: 'Synthesis Report: Solid State Batteries',
    description: 'Contains citations from 12 recent papers regarding energy density improvements.',
    query: 'Analyze solid state lithium metal electrolytes, dendrite suppression, and volumetric energy density metrics.',
    mode: 'quick',
    createdAt: '2026-10-24T09:00:00Z',
    updatedAt: '2026-10-24T09:30:00Z',
    dateLabel: 'Oct 24',
    status: 'draft',
    category: 'Energy & Materials',
    isStarred: false,
    isShared: false,
    messages: [
      {
        id: 'msg-bat-1',
        role: 'user',
        content: 'Analyze solid state lithium metal electrolytes, dendrite suppression, and volumetric energy density metrics.',
        timestamp: '9:00 AM'
      },
      {
        id: 'msg-bat-2',
        role: 'assistant',
        title: 'Synthesis Report: Solid State Batteries',
        content: 'Solid-state electrolytes (SSEs) utilizing sulfide and garnet-type ceramics show volumetric energy densities exceeding 900 Wh/L while mitigating thermal runaway risks.',
        timestamp: '9:05 AM',
        sections: [
          {
            heading: 'Dendrite Growth Mitigation',
            body: 'Interfacial engineered thin coatings (e.g., ALD ZnO layers) regulate lithium deposition and prevent short-circuiting during rapid charge cycles.'
          }
        ]
      }
    ],
    sources: [
      {
        id: 'src-b1',
        index: 1,
        title: 'Sulfide-based solid electrolytes for high-rate lithium batteries',
        authors: 'Kim, Y., Park, S.',
        year: 2024,
        journal: 'Advanced Energy Materials',
        relevance: 0.96,
        doi: '10.1002/aenm.2024',
        tags: ['Peer Reviewed'],
        abstract: 'Ionic conductivity optimization exceeding 10-2 S/cm at room temperature.'
      }
    ],
    attachedFiles: []
  },
  {
    id: 'neural-plasticity-pdf',
    title: 'Literature Review - Neural Plasticity.pdf',
    description: 'Annotated PDF source file detailing synaptic potentiation and cortical remapping.',
    query: 'Literature review on synaptic plasticity, long-term potentiation, and cortical remapping following ischemia.',
    mode: 'deep',
    createdAt: '2026-10-22T11:20:00Z',
    updatedAt: '2026-10-22T11:20:00Z',
    dateLabel: 'Oct 22',
    status: 'completed',
    category: 'Neuroscience',
    isStarred: false,
    isShared: false,
    messages: [],
    sources: [],
    attachedFiles: [
      {
        id: 'f-pdf-1',
        name: 'Neural Plasticity.pdf',
        size: '4.2 MB',
        type: 'application/pdf'
      }
    ]
  },
  {
    id: 'climate-data-sets-chat',
    title: 'Chat Session: Analyzing Climate Data Sets',
    description: 'Discussion thread parsing CSV anomaly data and temperature variance.',
    query: 'Help me parse global surface temperature anomaly CSV files and plot 10-year rolling averages.',
    mode: 'quick',
    createdAt: '2026-10-15T16:00:00Z',
    updatedAt: '2026-10-15T16:45:00Z',
    dateLabel: 'Oct 15',
    status: 'completed',
    category: 'Data Analytics',
    isStarred: false,
    isShared: true,
    messages: [],
    sources: [],
    attachedFiles: [
      {
        id: 'f-csv-1',
        name: 'Global_Temp_Anomalies_2024.csv',
        size: '1.8 MB',
        type: 'text/csv'
      }
    ]
  }
];

export const INITIAL_COLLECTIONS: Collection[] = [
  {
    id: 'col-quantum',
    title: 'Quantum Materials Analysis',
    refsCount: 14,
    updatedAgo: '2d ago',
    icon: 'biotech',
    category: 'Physics & Computing',
    projectIds: ['quantum-2024']
  },
  {
    id: 'col-synbio',
    title: 'Synthetic Biology Ethics',
    refsCount: 8,
    updatedAgo: '5d ago',
    icon: 'eco',
    category: 'Bioengineering',
    projectIds: []
  },
  {
    id: 'col-ml-bias',
    title: 'Machine Learning Bias Models',
    refsCount: 32,
    updatedAgo: '1w ago',
    icon: 'data_usage',
    category: 'Artificial Intelligence',
    projectIds: []
  }
];

export const SUGGESTED_VECTORS = [
  {
    id: 'vec-1',
    title: 'Recent breakthroughs in carbon capture',
    description: 'Analyze literature from the past 24 months focusing on direct air capture efficiency metrics.',
    icon: 'science',
    query: 'Analyze literature from the past 24 months focusing on direct air capture efficiency metrics and carbon capture breakthroughs.'
  },
  {
    id: 'vec-2',
    title: 'Economic impact of remote work',
    description: 'Synthesize data on urban commercial real estate depreciation vs suburban economic growth.',
    icon: 'monitoring',
    query: 'Synthesize data on urban commercial real estate depreciation vs suburban economic growth as a result of remote work.'
  },
  {
    id: 'vec-3',
    title: 'CRISPR off-target toxicity reduction',
    description: 'Evaluate high-fidelity Cas9 variants and prime editing efficiency in mammalian germlines.',
    icon: 'biotech',
    query: 'Evaluate recent advancements in high-fidelity Cas9 variants, prime editing, and off-target toxicity reduction in mammalian cells.'
  },
  {
    id: 'vec-4',
    title: 'Solid state battery interfacial impedance',
    description: 'Review electrolyte-anode boundary chemistry and dendrite growth prevention in sulfide cells.',
    icon: 'bolt',
    query: 'Review solid state battery interfacial impedance, electrolyte-anode boundary chemistry, and dendrite growth suppression.'
  }
];
