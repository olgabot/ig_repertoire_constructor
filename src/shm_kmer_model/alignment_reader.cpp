//
// Created by Andrew Bzikadze on 5/18/16.
//

#include <tuple>
#include <string>

#include <seqan/seq_io.h>

#include "alignment_reader.hpp"
#include "gene_alignment.hpp"

using namespace ns_gene_alignment;
using namespace ns_alignment_reader;

AlignmentReader::AlignmentReader(const std::string &alignments_filename,
                                 const shm_config::alignment_checker_params &alignment_checker_params,
                                 const shm_config::alignment_cropper_params &alignment_cropper_params) :
    alignments_filename_(alignments_filename)
{
    using AlignmentCheckerMethod = shm_config::alignment_checker_params::AlignmentCheckerMethod;
    if (alignment_checker_params.alignment_checker_method == AlignmentCheckerMethod::NoGapsAlignmentChecker) {
        alignment_checker_ptr_ = std::make_shared<NoGapsAlignmentChecker>
            (NoGapsAlignmentChecker(alignment_checker_params));
    }

    using AlignmentCropperMethod = shm_config::alignment_cropper_params::AlignmentCropperMethod;
    if (alignment_cropper_params.alignment_cropper_method == AlignmentCropperMethod::UptoLastReliableKMer) {
        alignment_cropper_ptr_ = std::make_shared<UptoLastReliableKmerAlignmentCropper>
            (UptoLastReliableKmerAlignmentCropper(alignment_cropper_params.rkmp));
    }
}

ns_gene_alignment::VectorReadGermlinePairs AlignmentReader::read_alignments() {
    std::vector<seqan::CharString> names;
    std::vector<seqan::CharString> reads;
    seqan::SeqFileIn seqFileIn(alignments_filename_.c_str());
    seqan::readRecords(names, reads, seqFileIn);
    VectorReadGermlinePairs alignments;
    alignments.reserve(reads.size());

    auto ReadIterator = reads.cbegin();
    while(ReadIterator != reads.cend()) {
        std::string germline_seq = std::string(seqan::toCString(*ReadIterator));
        ++ReadIterator;
        assert(ReadIterator != reads.cend());
        std::string read_seq = std::string(seqan::toCString(*ReadIterator));
        ReadGermlinePair alignment(std::move(germline_seq), std::move(read_seq));
        if (alignment_checker_ptr_ -> check(alignment)) {
            std::cout << alignment.first << std::endl;
            std::cout << alignment.second << std::endl;
            alignment_cropper_ptr_ -> crop(alignment);
            std::cout << alignment.first << std::endl;
            std::cout << alignment.second << std::endl << std::endl;
            alignments.emplace_back(std::move(alignment));
        }
        ++ReadIterator;
    }
    return alignments;
}
