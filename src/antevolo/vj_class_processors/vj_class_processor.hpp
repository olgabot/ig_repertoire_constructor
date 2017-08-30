#pragma once

#include <decomposition.hpp>
#include <antevolo_config.hpp>
#include "base_vj_class_processor.hpp"
#include "cdr3_hamming_graph_connected_components_processors/kruskal_cdr3_hg_cc_processor.hpp"
#include <shm_model_utils/shm_model_edge_weight_calculator.hpp>

namespace antevolo {
    class VJClassProcessor : public BaseCandidateCalculator {

        const AntEvoloConfig &config_;
        size_t num_mismatches_;
        const AnnotatedCloneByReadConstructor &clone_by_read_constructor_;
        size_t current_fake_clone_index_;
        size_t reconstructed_;
        typedef std::map<std::pair<std::string, std::string>, std::vector<size_t>> UniqueCDR3JNuclIndexMap;
        typedef std::map<std::string, size_t> CDR3ToIndexMap;
        typedef boost::associative_property_map<std::map<size_t, size_t>> AP_map;

        UniqueCDR3JNuclIndexMap unique_cdr3sJnucl_map_;
        CDR3ToIndexMap cdr3_to_old_index_map_;
        std::vector<std::string> unique_cdr3s_;

        SparseGraphPtr sparse_cdr_graph_;
        GraphComponentMap graph_component_map_;

        void Clear();

        std::string GetFastaFname(core::DecompositionClass decomposition_class);

    public:
        VJClassProcessor(CloneSetWithFakesPtr clone_set,
                         const AntEvoloConfig &config,
                         const AnnotatedCloneByReadConstructor &clone_by_read_constructor,
                         size_t current_fake_clone_index) :
                BaseCandidateCalculator(clone_set),
                config_(config),
                num_mismatches_(config.algorithm_params.similar_cdr3s_params.num_mismatches),
                clone_by_read_constructor_(clone_by_read_constructor),
                current_fake_clone_index_(current_fake_clone_index),
                reconstructed_(0) {}

        void CreateUniqueCDR3Map(core::DecompositionClass decomposition_class);

        std::string WriteUniqueCDR3InFasta(core::DecompositionClass decomposition_class);

        std::string GetJNucleotides(const annotation_utils::AnnotatedClone &);

        void CreateUniqueCDR3JNucleotidesMap(core::DecompositionClass decomposition_class);


        std::string GetGraphFname(core::DecompositionClass decomposition_class);

        std::vector<SparseGraphPtr> ComputeCDR3HammingGraphs(std::string cdr_fasta, std::string cdr_graph);

        void
        ComputeCDR3JNucleotidesHammingGraphs(double tau, std::string cdr_graph);

        void dfs(int v, bool *used, std::vector<int> &components_helper,
                         std::vector<std::pair<string, string>> const &unique_cdr3Jnucl, double tau);

        void ProcessComponentWithKruskal(SparseGraphPtr hg_component, size_t component_id);

        void ProcessComponentWithEdmonds(SparseGraphPtr hg_component, size_t component_id,
                                         const ShmModelEdgeWeightCalculator &edge_weight_calculator);

        double CDR3JNucleotidesDistance(const std::pair<string, string> &, const std::pair<string, string> &);

        size_t GetCurrentFakeCloneIndex() const { return current_fake_clone_index_; };

        size_t GetNumberOfReconstructedClones() const { return reconstructed_; };

        void HG_components(SparseGraphPtr hg_component, size_t component_id,
                           const ShmModelEdgeWeightCalculator &edge_weight_calculator);


    };
}