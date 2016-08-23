#pragma once

#include "evolutionary_graph_utils/evolutionary_tree.hpp"
#include "evolutionary_annotated_shm.hpp"
#include "tree_based_shm_annotator.hpp"

namespace antevolo {
    class AnnotatedEvolutionaryTree {
        const annotation_utils::CDRAnnotatedCloneSet* clone_set_prt_;
        const EvolutionaryTree *tree_ptr_;
        TreeBasedSHMAnnotator shm_annotator_;

        std::map<size_t, std::vector<EvolutionaryAnnotatedSHM> > unique_shms_;
        std::vector<EvolutionaryAnnotatedSHM> all_unique_shms_;

        void CheckConsistencyFatal(size_t clone_id);

    public:
        AnnotatedEvolutionaryTree(const annotation_utils::CDRAnnotatedCloneSet &clone_set,
                                  const EvolutionaryTree &tree) : clone_set_prt_(&clone_set),
                                                                  tree_ptr_(&tree),
                                                                  shm_annotator_(clone_set, tree) { }

        void AddSHMForClone(size_t clone_id, annotation_utils::SHM shm);

        const EvolutionaryTree& Tree() const { return *tree_ptr_; }

        size_t NumUniqueSHms() const { return all_unique_shms_.size(); }

        size_t NumSynonymousSHMs() const;

        size_t NumSynonymousWrtGermlineSHMs() const;

        size_t RootDepth() const;

        size_t NumAddedSHMs() const; // return numner of SHMs that were added wrt to tree root

        typedef std::vector<EvolutionaryAnnotatedSHM>::const_iterator SHMConstIterator;

        SHMConstIterator cbegin() const { return all_unique_shms_.cbegin(); }

        SHMConstIterator cend() const { return all_unique_shms_.cend(); }
    };
}